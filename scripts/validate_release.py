#!/usr/bin/env python3
"""Offline development checks and deterministic archive construction, not mail setup."""
import argparse
import ast
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sync_skill import synchronize
from privacy_checks import check_text as privacy_text, check_git_metadata, collect_git_metadata
from release_evidence import (ci_export, failure_export, provenance, tool_versions, utc_now)
from conformance import check_corpus

PUBLIC_ROOT = {".gitattributes", ".gitignore", "README.md", "CHANGELOG.md", "LICENSE", "PROTOCOL.md", "SECURITY.md",
               "install.py", "install.command", "release.json", "requirements-checks.txt"}
PUBLIC_DIRS = {".github", "assets", "docs", "examples", "schemas", "skills", "scripts", "templates", "tests"}
BLOCKED_PARTS = {"local", ".git", ".hg", ".svn", "__pycache__", "__MACOSX", ".venv", "node_modules", "backups", ".pytest_cache"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def public_files(root):
    """Allow public source only; never silently bundle private/cache directories."""
    root = Path(root)
    files = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if relative.parts[0] == ".git":
            continue
        if path.is_symlink():
            raise ValueError("Symbolic link in release source: " + relative.as_posix())
        if any(part in BLOCKED_PARTS or part.startswith(".env") for part in relative.parts):
            raise ValueError("Private or cache path in release source: " + relative.as_posix())
        metadata = path.name in (".DS_Store", "Thumbs.db", "desktop.ini") or path.name.startswith("._")
        if metadata and path.is_dir():
            raise ValueError("An OS metadata name must not hide a directory")
        if metadata:
            continue
        if relative.parts[0] not in PUBLIC_ROOT | PUBLIC_DIRS:
            raise ValueError("Unapproved release root path: " + relative.as_posix())
        if path.is_file():
            files.append(path)
    return files


def inspect_png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid PNG signature")
    offset, names = 8, []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data) or zlib.crc32(data[offset + 4:end - 4]) & 0xffffffff != struct.unpack(">I", data[end - 4:end])[0]:
            raise ValueError("Invalid PNG chunk")
        names.append(kind.decode("ascii"))
        if kind in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            raise ValueError("Unexpected PNG text/EXIF metadata")
        offset = end
        if kind == b"IEND":
            break
    if offset != len(data) or not names or names[-1] != "IEND":
        raise ValueError("PNG trailing bytes or missing end")
    return {"pixels": list(struct.unpack(">II", data[16:24])), "chunks": names}


def check_text(text, relative):
    privacy_text(text, relative)


def release_metadata(root):
    release = json.loads((Path(root) / "release.json").read_text())
    if not isinstance(release, dict) or not isinstance(release.get("version"), str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-en", release["version"]):
        raise ValueError("Invalid package version; path separators are not permitted")
    if (release.get("project"), release.get("author"), release.get("skill_id"), release.get("license")) != (
            "Agentlogue", "Alexander C. H. Lou", "agent-filing-protocol", "MIT"):
        raise ValueError("Project identity or license metadata changed")
    return release


def check_source(root):
    root = Path(root)
    release = release_metadata(root)
    for name in PUBLIC_ROOT:
        if not (root / name).is_file():
            raise ValueError("Required public source file missing: " + name)
    count = synchronize(root, check=True)
    if sha((root / "PROTOCOL.md").read_bytes()) != release["protocol_sha256"]:
        raise ValueError("Canonical protocol bytes differ from pinned revision")
    version = release["version"]
    markers = {"README.md": "v" + version, "docs/installation.md": "v" + version,
               "docs/conversation-map.md": "v" + version,
               "skills/agent-filing-protocol/SKILL.md": 'version: "' + version + '"',
               "skills/agent-filing-protocol/references/licensing.md": "v" + version,
               "assets/agent-conversation-map.svg": "PACKAGE v" + version.upper()}
    for file, marker in markers.items():
        if marker not in (root / file).read_text():
            raise ValueError("Package-version marker missing: " + file)
    if (root / "LICENSE").read_bytes() != (root / "skills/agent-filing-protocol/LICENSE").read_bytes():
        raise ValueError("License copies differ")
    notice = next(line for line in (root / "LICENSE").read_text().splitlines() if line.startswith("Copyright "))
    quoted = re.search(r'The retained copyright notice is:\s*```text\n([^\n]+)\n```', (root / "README.md").read_text())
    if not quoted or quoted.group(1) != notice:
        raise ValueError("README retained copyright quotation differs from LICENSE")
    config = json.loads((root / "skills/agent-filing-protocol/assets/config.example.json").read_text())
    fixed = {"config_version": 1, "protocol_version": "AFP v1.3", "language_edition": "en",
             "role": "preparer", "content_mode": "minimal_reference", "mail_provider": "gmail"}
    for field, value in config.items():
        if (field in fixed and value != fixed[field]) or (field not in fixed and value):
            raise ValueError("Configuration template contains deployment settings")
    spec = importlib.util.spec_from_file_location("release_setup_checks", root / "skills/agent-filing-protocol/scripts/afp_setup.py")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    if config != runtime.DEFAULT_CONFIG or runtime.verify_bundle(root / "skills/agent-filing-protocol") != count:
        raise ValueError("Runtime defaults or manifest verification disagree with release checks")
    inventory, corpus, links = [], [], 0
    for path in public_files(root):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        inventory.append({"path": relative, "bytes": len(data), "sha256": sha(data)})
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            if relative != "assets/agent-conversation-map.png":
                raise ValueError("Unexpected binary release file: " + relative)
            inspect_png(data)
            continue
        check_text(text, relative)
        corpus.append("# SOURCE: " + relative + "\n" + text)
        if path.suffix == ".md":
            prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", prose):
                target = target.split("#", 1)[0].split(" ", 1)[0]
                if not target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                    continue
                links += 1
                if not (path.parent / target).is_file():
                    raise ValueError("Missing relative Markdown path in " + relative)
        if path.suffix == ".py":
            ast.parse(text, feature_version=9)
    svg = ET.fromstring((root / "assets/agent-conversation-map.svg").read_text())
    for node in svg.iter():
        if node.tag.rsplit("}", 1)[-1] in ("script", "foreignObject"):
            raise ValueError("Active SVG content")
        for key, value in node.attrib.items():
            if key.lower().startswith("on") or key.rsplit("}", 1)[-1] == "href":
                raise ValueError("SVG event handler or external reference")
    png = inspect_png((root / "assets/agent-conversation-map.png").read_bytes())
    if png["pixels"] != [2400, 2420] or float(svg.attrib["width"]) / float(svg.attrib["height"]) != 2400 / 2420:
        raise ValueError("Diagram geometry differs")
    for file in (root / "templates/filing-email.md", root / "examples/example-filing.md"):
        if "From: <SENDING_ACCOUNT>\nTo: <LEDGER_EMAIL>" not in file.read_text():
            raise ValueError("Sender and ledger envelope mismatch")
    return {"release": release, "manifest_files": count, "relative_paths_checked": links,
            "png": png, "inventory": inventory}, "\n\n".join(corpus)


def schema_checks(root):
    from jsonschema import Draft202012Validator
    from referencing import Registry
    schema = json.loads((Path(root) / "schemas/filing-summary.schema.json").read_text())
    example = json.loads((Path(root) / "examples/example-summary.json").read_text())
    def refuse(uri):
        raise ValueError("External schema retrieval is forbidden")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, registry=Registry(retrieve=refuse))
    validator.validate(example)
    controls = []
    missing = copy.deepcopy(example); missing.pop("matter_id"); controls.append(missing)
    extra = copy.deepcopy(example); extra["unknown"] = True; controls.append(extra)
    mixed = copy.deepcopy(example); mixed["evidence"]["materials_read"] = ["none", "filing"]; controls.append(mixed)
    correction = copy.deepcopy(example); correction["filing_type"] = "correction"; controls.append(correction)
    if not all(list(validator.iter_errors(control)) for control in controls):
        raise ValueError("Schema negative control failed")
    return {"draft": "2020-12", "example_valid": True, "negative_controls_rejected": len(controls), "external_retrieval": "refused"}


def scan_corpus(binary, root, corpus, output):
    version = subprocess.run([str(binary), "version"], capture_output=True, text=True, timeout=15)
    if version.returncode or version.stdout.strip() != "8.30.1":
        raise ValueError("Release checks require the pinned Gitleaks 8.30.1 binary")
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GITLEAKS")}
    with tempfile.TemporaryDirectory(prefix="agentlogue-scan-") as temporary:
        temp = Path(temporary)
        for label, text, expected in [("public", corpus, 0),
                                      ("synthetic-control", 'token = "' + 'ghp_' + 'Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56Qr78' + '"', 1)]:
            folder = temp / label; folder.mkdir()
            (folder / "corpus.txt").write_text(text)
            report = output / ("gitleaks-" + label + ".json")
            command = [str(binary), "dir", str(folder), "--config", str(Path(root) / "scripts/gitleaks.toml"),
                       "--redact=100", "--no-banner", "--no-color", "--ignore-gitleaks-allow",
                       "--gitleaks-ignore-path", str(temp / "no-ignore-file"), "--max-decode-depth", "5",
                       "--max-archive-depth", "3", "--report-format", "json", "--report-path", str(report), "--exit-code", "17"]
            result = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=55)
            (output / ("gitleaks-" + label + ".log")).write_text(result.stdout + result.stderr)
            findings = json.loads(report.read_text()) if report.exists() else None
            if findings is None or len(findings) != expected or result.returncode != (17 if expected else 0):
                raise ValueError("Secret scan or its negative control failed: " + label)
    return {"gitleaks_version": "8.30.1", "public_findings": 0, "synthetic_control_findings": 1,
            "scope": "All UTF-8 public source, including SVG; PNG structure/metadata inspected separately"}


def build_archives(root, output, inventory):
    root, output = Path(root), Path(output)
    if root.resolve() == output.resolve() or root.resolve() in output.resolve().parents:
        raise ValueError("Build output must be outside the source tree")
    release = release_metadata(root)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.fromisoformat(release["archive_timestamp"].replace("Z", "+00:00"))
    checksums, archives = [], []
    for kind, prefix, sub in [("github", "agentlogue", ""), ("skill", "agent-filing-protocol", "skills/agent-filing-protocol/")]:
        path = output / ("agentlogue-v" + release["version"] + "-" + kind + ".zip")
        chosen = [row for row in inventory if not sub or row["path"].startswith(sub)]
        with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for row in chosen:
                source = root / row["path"]
                data = source.read_bytes()
                if sha(data) != row["sha256"]:
                    raise ValueError("Source changed during build: " + row["path"])
                relative = row["path"][len(sub):]
                entry = zipfile.ZipInfo(prefix + "/" + relative, stamp.timetuple()[:6])
                entry.create_system = 3
                entry.external_attr = (stat.S_IFREG | (0o755 if source.stat().st_mode & 0o111 else 0o644)) << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(path) as archive:
            expected = {prefix + "/" + row["path"][len(sub):]: row["sha256"] for row in chosen}
            if archive.testzip() or len(archive.namelist()) != len(set(archive.namelist())) or archive.comment:
                raise ValueError("Invalid release archive")
            if {name: sha(archive.read(name)) for name in archive.namelist()} != expected:
                raise ValueError("Archive/source byte mismatch")
            for entry in archive.infolist():
                if entry.extra or entry.comment or entry.flag_bits & 1 or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError("Unexpected ZIP member metadata")
        checksum = sha(path.read_bytes())
        checksums.append(checksum + "  " + path.name)
        archives.append({"file": path.name, "sha256": checksum, "files": len(chosen), "bytes": path.stat().st_size})
    with (output / "SHA256SUMS.txt").open("xb") as stream:
        stream.write(("\n".join(checksums) + "\n").encode("utf-8"))
    with (output / "SOURCE-MANIFEST.json").open("xb") as stream:
        stream.write((json.dumps(inventory, indent=2) + "\n").encode("utf-8"))
    return archives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gitleaks", type=Path, required=True, help="Verified Gitleaks 8.30.1 executable")
    parser.add_argument("--output", type=Path, required=True, help="New validation evidence directory outside source")
    parser.add_argument("--artifacts", type=Path, help="New archive directory outside source")
    parser.add_argument("--ci-export", type=Path, help="New allowlisted public CI evidence directory outside source")
    args = parser.parse_args()
    stage = "setup"
    started = utc_now()
    try:
        for path in (args.output, args.artifacts, args.ci_export):
            if path and (ROOT.resolve() == path.resolve() or ROOT.resolve() in path.resolve().parents):
                raise ValueError("Validation outputs must be outside source")
        if args.ci_export and (args.ci_export.exists() or args.ci_export.is_symlink()):
            raise ValueError("CI export destination must be new")
        args.output.mkdir(parents=True, exist_ok=False)
        stage = "source"
        source, corpus = check_source(ROOT)
        identity = provenance(ROOT)
        stage = "tests"
        tests = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts/run_tests.py"),
                                "--output", str(args.output / "tests-result.json"), "--log", str(args.output / "tests.log")],
                               cwd=ROOT, capture_output=True, text=True, timeout=55)
        if tests.returncode:
            raise ValueError("Regression tests failed; see tests.log")
        test_result = json.loads((args.output / "tests-result.json").read_text())
        stage = "schema"
        schemas = schema_checks(ROOT)
        stage = "privacy"
        metadata = check_git_metadata(ROOT)
        git_text = collect_git_metadata(ROOT)
        if git_text is not None:
            corpus += "\n\n# REACHABLE LOCAL GIT METADATA\n" + git_text
        scans = scan_corpus(args.gitleaks, ROOT, corpus, args.output)
        scans["reachable_git_metadata_included"] = git_text is not None
        stage = "conformance"
        conformance = check_corpus(json.loads((ROOT / "examples/conformance/cases.json").read_text()))
        after, _ = check_source(ROOT)
        if after["inventory"] != source["inventory"]:
            raise ValueError("Source changed while checks ran")
        stage = "archives"
        archives = build_archives(ROOT, args.artifacts, source["inventory"]) if args.artifacts else []
        report = {**source, "status": "passed", "schema": schemas, "secrets": scans, "tests": test_result,
                  "checks": {"source": "passed", "tests": "passed", "schema": "passed", "privacy": "passed",
                             "git_metadata": metadata["status"], "conformance": "passed",
                             "archives": "passed" if args.artifacts else "not_run"},
                  "conformance": conformance, "provenance": identity, "tools": tool_versions(),
                  "started_at_utc": started, "completed_at_utc": utc_now(), "candidate_only": True,
                  "archives": archives, "python": sys.version.split()[0], "zlib": zlib.ZLIB_VERSION,
                  "limits": "Local synthetic checks; no live mail, native-host, publisher-identity or legal-compliance certification"}
        (args.output / "VALIDATION-REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
        stage = "report_export"
        if args.ci_export:
            ci_export(report, args.artifacts, args.ci_export)
        print(json.dumps({"version": source["release"]["version"], "source_files": len(source["inventory"]),
                          "manifest_files": source["manifest_files"], "tests": test_result["counts"], "secret_findings": 0,
                          "archives": archives}, indent=2))
    except (OSError, ValueError, ImportError, subprocess.SubprocessError):
        if args.ci_export and ROOT.resolve() not in args.ci_export.resolve().parents and args.ci_export.resolve() != ROOT.resolve():
            try:
                failure_export(args.ci_export, stage)
            except OSError:
                pass
        print("Release validation failed at stage: " + stage + "; candidate validation is incomplete.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
