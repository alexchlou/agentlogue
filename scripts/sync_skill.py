#!/usr/bin/env python3
"""Generate/check portable resources and manifest from explicit canonical inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
MAPPING = {
    "PROTOCOL.md": "references/PROTOCOL.md",
    "SECURITY.md": "references/SECURITY.md",
    "LICENSE": "LICENSE",
    "templates/filing-email.md": "assets/filing-email.md",
    "templates/registry-entry.md": "assets/registry-entry.md",
    "schemas/filing-summary.schema.json": "references/filing-summary.schema.json",
    "examples/example-filing.md": "references/example-filing.md",
    "examples/example-summary.json": "references/example-summary.json",
    "examples/materials/submission-demo.txt": "references/materials/submission-demo.txt",
    "docs/privacy.md": "references/privacy.md",
}


def metadata_name(name):
    return name in (".DS_Store", "Thumbs.db", "desktop.ini") or name.startswith("._")


def synchronize(root, check=False):
    root = Path(root)
    skill = root / "skills/agent-filing-protocol"
    if skill.is_symlink() or (skill / "local").exists() or (skill / "local").is_symlink():
        raise ValueError("Use a clean public source tree, never an installed Skill")
    for path in skill.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symbolic links are not permitted in the public Skill")
        if path.is_dir() and metadata_name(path.name):
            raise ValueError("An OS metadata name must not hide a directory")
    for original, relative in MAPPING.items():
        source, target = root / original, skill / relative
        if source.is_symlink() or target.is_symlink():
            raise ValueError("Canonical resources must not be symbolic links")
        data = source.read_bytes()
        if check:
            if not target.is_file() or target.read_bytes() != data:
                raise ValueError("Resource copy differs: " + relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    manifest = {p.relative_to(skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(skill.rglob("*"), key=lambda p: p.relative_to(skill).as_posix())
                if p.is_file() and p.relative_to(skill).as_posix() != "MANIFEST.json"
                and not metadata_name(p.name)}
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    if check:
        if (skill / "MANIFEST.json").read_bytes() != encoded:
            raise ValueError("Skill manifest is stale; run scripts/sync_skill.py")
    else:
        (skill / "MANIFEST.json").write_bytes(encoded)
    return len(manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps({"manifest_files": synchronize(ROOT, args.check), "mode": "check" if args.check else "generate"}))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
