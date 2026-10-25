#!/usr/bin/env python3
"""Offline owner-settings helper. No mail, network, OAuth, or platform edits."""
import sys

if sys.version_info < (3, 9):
    sys.exit("AFP setup requires Python 3.9 or newer; no settings were changed.")

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

sys.dont_write_bytecode = True
SKILL_NAME = "agent-filing-protocol"
MAX_CONFIG_BYTES = 65536
SKILL_ROOT = Path(__file__).resolve().parents[1]
ROLES = ("preparer", "read_only_auditor", "independent_filer", "send_only_participant")
DEFAULT_CONFIG = {
    "config_version": 1, "protocol_version": "AFP v1.3", "language_edition": "en",
    "owner_name": "", "ledger_email": "", "sending_account": "", "agent_label": "",
    "role": "preparer", "authorized_matters": [], "material_scope": "",
    "trusted_approval_channel": "", "registry_location": "",
    "registry_write_authorized": False, "responsible_filer": "",
    "content_mode": "minimal_reference", "retention_policy": "",
    "mail_provider": "gmail", "readback_location": "", "authorized_reader": "",
}
# Inert metadata that Finder, Explorer, or archive tools add when a folder is browsed.
OS_METADATA_NAMES = (".DS_Store", "Thumbs.db", "desktop.ini")


def is_os_metadata(name):
    return name in OS_METADATA_NAMES or name.startswith("._")


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def load_config(path):
    """Read settings from a file, or from standard input when path is '-'."""
    if str(path) == "-":
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        value = stream.read(MAX_CONFIG_BYTES + 1)
        raw = value.encode("utf-8") if isinstance(value, str) else value
    else:
        path = Path(path).expanduser()
        with path.open("rb") as stream:
            raw = stream.read(MAX_CONFIG_BYTES + 1)
    if len(raw) > MAX_CONFIG_BYTES:
        raise ValueError("Configuration exceeds 64 KiB")
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates)
    validate_config(data)
    return data


def validate_config(data):
    if not isinstance(data, dict) or set(data) != set(DEFAULT_CONFIG):
        raise ValueError("Use exactly the keys in assets/config.example.json; do not store credentials")
    for key, default in DEFAULT_CONFIG.items():
        if type(data[key]) is not type(default):
            raise ValueError("Wrong configuration type: " + key)
        if isinstance(default, str):
            value = data[key]
            if len(value) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise ValueError("Control characters or excessive length in: " + key)
    if data["config_version"] != 1 or data["protocol_version"] != "AFP v1.3" or data["language_edition"] != "en":
        raise ValueError("Unsupported configuration or protocol edition")
    if data["role"] not in ROLES:
        raise ValueError("Unsupported role; use one of: " + ", ".join(ROLES))
    if data["content_mode"] not in ("minimal_reference", "full_content"):
        raise ValueError("Unsupported content mode")
    for key in ("ledger_email", "sending_account"):
        if data[key] and not re.fullmatch(r"[^\s@<>,;]+@[^\s@<>,;]+\.[^\s@<>,;]+", data[key]):
            raise ValueError("Expected one plain email address in: " + key)
    label = data["agent_label"]
    if label and not re.fullmatch(r".+ \([^()]+\)", label):
        raise ValueError("agent_label needs a platform suffix, for example Muse (Owner platform)")
    matters = data["authorized_matters"]
    if len(matters) > 200 or any(type(m) is not str or not m.strip() or len(m) > 512 or any(ord(c) < 32 or ord(c) == 127 for c in m) for m in matters):
        raise ValueError("authorized_matters must contain bounded nonempty text entries")
    if len(set(matters)) != len(matters):
        raise ValueError("authorized_matters contains duplicates")


def settings_report(data):
    validate_config(data)
    required = ["owner_name", "ledger_email", "agent_label", "authorized_matters",
                "material_scope", "trusted_approval_channel", "registry_location",
                "responsible_filer", "retention_policy"]
    if data["role"] in ("independent_filer", "send_only_participant"):
        required += ["sending_account", "readback_location"]
    if data["role"] == "send_only_participant":
        required += ["authorized_reader"]
    missing = [k for k in required if not data[k] or isinstance(data[k], str) and not data[k].strip()]
    return {
        "configuration_state": "incomplete" if missing else "locally_complete",
        "missing_fields": missing, "role": data["role"],
        "protocol_adoption": "requires_trusted_owner_instruction",
        "runtime_capabilities": "not_observed",
        "mail_connector": "not_configured_by_this_helper",
        "per_message_approval": "required", "ready_to_send": False,
    }


def verify_bundle(root):
    """Detect accidental changes, not publisher authenticity or runtime safety."""
    root = Path(root)
    manifest = root / "MANIFEST.json"
    if root.is_symlink() or manifest.is_symlink():
        raise ValueError("Skill root and manifest must not be symbolic links")
    expected = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Invalid skill manifest")
    actual = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if path.is_symlink():
            raise ValueError("Symbolic link in skill: " + rel.as_posix())
        if rel.parts[0] == "local" or (path.is_file() and is_os_metadata(path.name)):
            continue
        if path.is_file() and rel.as_posix() != "MANIFEST.json":
            actual[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        groups = (
            ("changed", sorted(k for k in actual.keys() & expected.keys() if actual[k] != expected[k])),
            ("unexpected", sorted(actual.keys() - expected.keys())),
            ("missing", sorted(expected.keys() - actual.keys())),
        )
        details = "; ".join(label + ": " + ", ".join(names[:5]) + (", ..." if len(names) > 5 else "")
                            for label, names in groups if names)
        raise ValueError("Skill files differ from MANIFEST.json (" + details + ")")
    return len(actual)


def ask(data, key, prompt):
    """Ask until the answer is valid, so one typo does not discard earlier answers."""
    while True:
        value = input(prompt + ": ").strip()
        if key == "authorized_matters":
            value = [v.strip() for v in value.split(";") if v.strip()]
        elif not value:
            return
        candidate = dict(data)
        candidate[key] = value
        try:
            validate_config(candidate)
        except ValueError as exc:
            print(str(exc) + ". Please enter it again.")
            continue
        data[key] = value
        return


def wizard():
    if not sys.stdin.isatty():
        raise ValueError("The wizard needs a terminal; use --config for noninteractive setup")
    data = dict(DEFAULT_CONFIG)
    print("AFP local setup. No passwords or tokens. Blank fields can be completed later.")
    prompts = [
        ("owner_name", "Owner name"), ("ledger_email", "Owner-controlled ledger email"),
        ("agent_label", "Agent label including platform, e.g. Muse (Owner platform)"),
        ("role", "Role: preparer, read_only_auditor, independent_filer, send_only_participant [preparer]"),
        ("authorized_matters", "Authorized matters (separate with semicolons; empty means no matters)"),
        ("material_scope", "Authorized material scope"),
        ("trusted_approval_channel", "Trusted owner approval channel"),
        ("registry_location", "Registry location, or 'owner chat only'"),
        ("responsible_filer", "Responsible filer label or matter-to-filer mapping"),
        ("retention_policy", "Retention period and owner-controlled handling"),
    ]
    for key, prompt in prompts:
        ask(data, key, prompt)
    if data["role"] in ("independent_filer", "send_only_participant"):
        for key, prompt in [("sending_account", "Sending account email"), ("readback_location", "Authorized read-back view")]:
            ask(data, key, prompt)
    if data["role"] == "send_only_participant":
        ask(data, "authorized_reader", "Authorized reader label")
    validate_config(data)
    print("Defaults: minimal_reference; registry writes require separate authorization.")
    return data


def check_private_path(path, directory=False):
    """Reject unsafe existing settings; doctor never silently changes permissions."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Refusing a symbolic-link private settings path")
    info = path.stat()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError("Private settings path has the wrong file type")
    if os.name == "posix":
        required = 0o700 if directory else 0o600
        if stat.S_IMODE(info.st_mode) != required or info.st_uid != os.getuid():
            raise ValueError("Private settings require owner-only permissions: local/ 0700, files 0600; review and repair permissions before retrying")


def check_local_settings(root):
    local = Path(root) / "local"
    if local.exists() or local.is_symlink():
        check_private_path(local, directory=True)
    path = local / "config.json"
    if path.exists() or path.is_symlink():
        check_private_path(path)
    return path


def publish_private(path, payload, replace=False):
    """Publish complete bytes. A hard link atomically refuses an existing name."""
    fd, temporary = tempfile.mkstemp(prefix=".config-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError:
                raise ValueError("Configuration or backup appeared during setup; refusing to overwrite")
            except OSError as exc:
                raise OSError("Atomic first creation requires hard-link support on this filesystem; no partial configuration was published") from exc
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_config(root, data, replace=False):
    validate_config(data)
    payload = (json.dumps(data, indent=2, ensure_ascii=True) + "\n").encode()
    if len(payload) > MAX_CONFIG_BYTES:
        raise ValueError("Configuration exceeds 64 KiB")
    path = check_local_settings(root)
    local = path.parent
    if path.exists() and not replace:
        raise ValueError("Local configuration already exists; use --replace to preserve a backup and change it")
    local.mkdir(mode=0o700, exist_ok=True)
    check_private_path(local, directory=True)
    backup = None
    if path.exists():
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = local / ("config.backup-" + stamp + "-" + uuid.uuid4().hex[:8] + ".json")
        publish_private(backup, path.read_bytes())
    publish_private(path, payload, replace=replace)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Read-only local integrity and configuration checks")
    configure = sub.add_parser("configure", help="Write local owner settings only")
    group = configure.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=Path, help="Settings JSON file, or '-' to read it from standard input")
    group.add_argument("--wizard", action="store_true", help="Prompt in a terminal")
    configure.add_argument("--replace", action="store_true", help="Preserve the existing config in a private backup")
    args = parser.parse_args()
    try:
        count = verify_bundle(SKILL_ROOT)
        path = check_local_settings(SKILL_ROOT)
        if args.command == "doctor":
            data = load_config(path) if path.exists() else dict(DEFAULT_CONFIG)
            report = settings_report(data)
            report["bundle_files_verified"] = count
            report["config_present"] = path.exists()
            print(json.dumps(report, indent=2))
            return 0 if report["configuration_state"] == "locally_complete" else 2
        if path.exists() and not args.replace:
            raise ValueError("Local configuration already exists; use --replace to preserve a backup and change it")
        data = wizard() if args.wizard else load_config(args.config)
        backup = write_config(SKILL_ROOT, data, replace=args.replace)
        report = settings_report(data)
        report.update({"action": "local_configuration_saved", "previous_config_preserved": bool(backup)})
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, EOFError) as exc:
        print("AFP setup: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
