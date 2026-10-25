#!/usr/bin/env python3
"""Install the AFP skill locally using only the Python standard library."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "skills/agent-filing-protocol"
sys.path.insert(0, str(SOURCE / "scripts"))
from afp_setup import DEFAULT_CONFIG, load_config, settings_report, verify_bundle, wizard, write_config


def default_destination(target):
    if target == "codex":
        return Path.home() / ".agents/skills/agent-filing-protocol"
    if target == "claude":
        return Path.home() / ".claude/skills/agent-filing-protocol"
    raise ValueError("Portable export requires --destination /path/agent-filing-protocol")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("codex", "claude", "portable"), default="codex")
    parser.add_argument("--destination", type=Path, help="Exact skill folder, ending in agent-filing-protocol")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--config", type=Path, help="Private owner-settings JSON, never credentials")
    group.add_argument("--wizard", action="store_true", help="Collect owner settings in the terminal")
    parser.add_argument("--dry-run", action="store_true", help="Show the plan without creating files")
    args = parser.parse_args(argv)
    stage = None
    lock = None
    locked = False
    try:
        count = verify_bundle(SOURCE)
        destination = (args.destination or default_destination(args.target)).expanduser().absolute()
        if destination.name != "agent-filing-protocol" or ".." in destination.parts:
            raise ValueError("Destination must be an explicit folder ending in agent-filing-protocol, without '..'")
        if destination.is_symlink():
            raise ValueError("Refusing a symbolic-link destination")
        data = wizard() if args.wizard else load_config(args.config) if args.config else dict(DEFAULT_CONFIG)
        report = settings_report(data)
        report.update({"target": args.target, "destination": str(destination), "bundle_files_verified": count})
        if args.dry_run:
            report["action"] = "dry_run"
            print(json.dumps(report, indent=2))
            return 0
        destination.parent.mkdir(parents=True, exist_ok=True)
        lock = destination.parent / ".agent-filing-protocol.install.lock"
        fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        locked = True
        os.close(fd)
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_dir():
                raise ValueError("Existing destination is not a regular skill directory")
            verify_bundle(destination)
            existing = json.loads((destination / "MANIFEST.json").read_text(encoding="utf-8"))
            source_manifest = json.loads((SOURCE / "MANIFEST.json").read_text(encoding="utf-8"))
            if existing != source_manifest:
                raise ValueError("A different skill version already exists; export to another folder and review migration")
            if args.config or args.wizard:
                raise ValueError("Skill already installed; use its configure command to change settings with a backup")
            path = destination / "local/config.json"
            report.update(settings_report(load_config(path) if path.exists() else dict(DEFAULT_CONFIG)))
            report["action"] = "already_installed_unchanged"
            print(json.dumps(report, indent=2))
            return 0
        stage = Path(tempfile.mkdtemp(prefix=".afp-stage-", dir=str(destination.parent)))
        shutil.copytree(SOURCE, stage, dirs_exist_ok=True)
        if (stage / "local").exists():
            raise ValueError("Source contains private local settings; use the clean release")
        write_config(stage, data)
        verify_bundle(stage)
        if destination.exists() or destination.is_symlink():
            raise ValueError("Destination appeared during setup; refusing to overwrite")
        stage.rename(destination)
        stage = None
        report["action"] = "installed_locally"
        report["next_step"] = "Invoke agent-filing-protocol in the host; establish trusted owner adoption and verify actual mail capabilities."
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, EOFError) as exc:
        print("AFP installer: " + str(exc), file=sys.stderr)
        return 1
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage)
        if locked and lock is not None:
            lock.unlink()


if __name__ == "__main__":
    sys.exit(main())
