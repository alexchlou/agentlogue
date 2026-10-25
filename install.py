#!/usr/bin/env python3
"""Install the AFP skill locally using only the Python standard library."""
import sys

if sys.version_info < (3, 9):
    sys.exit("AFP installer requires Python 3.9 or newer; no installation was performed.")

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "skills/agent-filing-protocol"
sys.path.insert(0, str(SOURCE / "scripts"))
from afp_setup import (DEFAULT_CONFIG, check_local_settings, is_os_metadata,
                       load_config, settings_report, verify_bundle, wizard, write_config)


def default_destination(target):
    if target == "codex":
        return Path.home() / ".agents/skills/agent-filing-protocol"
    if target == "claude":
        return Path.home() / ".claude/skills/agent-filing-protocol"
    raise ValueError("Portable export requires --destination /path/agent-filing-protocol")


def skip_os_metadata(directory, names):
    return [name for name in names if is_os_metadata(name)]


def existing_install(destination):
    """Refuse unrelated or changed installs before collecting owner settings."""
    if not (destination.exists() or destination.is_symlink()):
        return False
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError("Existing destination is not a regular skill directory")
    verify_bundle(destination)
    existing = json.loads((destination / "MANIFEST.json").read_text(encoding="utf-8"))
    expected = json.loads((SOURCE / "MANIFEST.json").read_text(encoding="utf-8"))
    if existing != expected:
        raise ValueError("A different skill version already exists; export to another parent directory and review migration")
    check_local_settings(destination)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("codex", "claude", "portable"), default="codex")
    parser.add_argument("--destination", type=Path, help="Exact skill folder, ending in agent-filing-protocol")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--config", type=Path, help="Private settings JSON, never credentials; '-' reads UTF-8 stdin")
    group.add_argument("--wizard", action="store_true", help="Collect owner settings in a terminal")
    parser.add_argument("--dry-run", action="store_true", help="Check the plan without creating files")
    args = parser.parse_args(argv)
    stage = None
    lock = None
    lock_identity = None
    status = 1
    report = None
    try:
        count = verify_bundle(SOURCE)
        if (SOURCE / "local").exists():
            raise ValueError("Source contains private local settings; use the clean release")
        destination = (args.destination or default_destination(args.target)).expanduser().absolute()
        if destination.name != "agent-filing-protocol" or ".." in destination.parts:
            raise ValueError("Destination must end in agent-filing-protocol, without '..'")
        present = existing_install(destination)
        if present and (args.config or args.wizard):
            raise ValueError("Skill already installed; use its configure command to change settings with a backup")
        if present:
            path = check_local_settings(destination)
            data = load_config(path) if path.exists() else dict(DEFAULT_CONFIG)
        else:
            data = wizard() if args.wizard else load_config(args.config) if args.config else dict(DEFAULT_CONFIG)
        report = settings_report(data)
        report.update(target=args.target, destination=str(destination), bundle_files_verified=count)
        if args.dry_run:
            report.update(action="dry_run", planned_action="already_installed_unchanged" if present else "install")
            print(json.dumps(report, indent=2))
            return 0
        destination.parent.mkdir(parents=True, exist_ok=True)
        lock = destination.parent / ".agent-filing-protocol.install.lock"
        try:
            fd = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise ValueError("Another installer holds the lock; investigate an abandoned lock before removing it")
        info = os.fstat(fd)
        lock_identity = (info.st_dev, info.st_ino)
        os.close(fd)
        if existing_install(destination) != present:
            raise ValueError("Destination changed during setup; refusing to overwrite")
        if present:
            # Re-read the current settings after locking; never report an earlier snapshot.
            path = check_local_settings(destination)
            report.update(settings_report(load_config(path) if path.exists() else dict(DEFAULT_CONFIG)))
            report["action"] = "already_installed_unchanged"
        else:
            stage = Path(tempfile.mkdtemp(prefix=".afp-stage-", dir=str(destination.parent)))
            shutil.copytree(SOURCE, stage, dirs_exist_ok=True, ignore=skip_os_metadata)
            write_config(stage, data)
            verify_bundle(stage)
            if destination.exists() or destination.is_symlink():
                raise ValueError("Destination appeared during setup; refusing to overwrite")
            stage.rename(destination)
            stage = None
            report.update(action="installed_locally", next_step="Invoke agent-filing-protocol in the host; establish trusted owner adoption and verify actual mail capabilities.")
        status = 0
    except (OSError, ValueError, EOFError) as exc:
        print("AFP installer: " + str(exc), file=sys.stderr)
    finally:
        # Staging cleanup must never prevent release of this run's own lock.
        try:
            if stage is not None and stage.exists():
                shutil.rmtree(stage)
        except OSError as exc:
            status = 1
            print("AFP installer: staging cleanup incomplete at " + str(stage) + ": " + str(exc), file=sys.stderr)
        finally:
            if lock_identity is not None:
                try:
                    info = lock.lstat()
                    if (info.st_dev, info.st_ino) != lock_identity:
                        raise ValueError("Install lock changed identity; leaving it for owner investigation")
                    lock.unlink()
                except (OSError, ValueError) as exc:
                    status = 1
                    print("AFP installer: lock cleanup incomplete: " + str(exc), file=sys.stderr)
    if status == 0:
        print(json.dumps(report, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
