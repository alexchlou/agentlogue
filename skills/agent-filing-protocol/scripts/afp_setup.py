#!/usr/bin/env python3
"""Offline owner-settings helper. No mail, network, OAuth, or platform edits."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
SKILL_NAME = "agent-filing-protocol"
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


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def load_config(path):
    path = Path(path).expanduser()
    if path.stat().st_size > 65536:
        raise ValueError("Configuration exceeds 64 KiB")
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
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
    if data["role"] not in ROLES or data["content_mode"] not in ("minimal_reference", "full_content"):
        raise ValueError("Unsupported role or content mode")
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
        if rel.parts[0] == "local":
            continue
        if path.is_file() and rel.as_posix() != "MANIFEST.json":
            actual[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("Skill files differ from MANIFEST.json; existing installs are never overwritten")
    return len(actual)


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
        value = input(prompt + ": ").strip()
        if key == "authorized_matters":
            data[key] = [v.strip() for v in value.split(";") if v.strip()]
        elif value:
            data[key] = value
    if data["role"] in ("independent_filer", "send_only_participant"):
        for key, prompt in [("sending_account", "Sending account email"), ("readback_location", "Authorized read-back view")]:
            data[key] = input(prompt + ": ").strip()
    if data["role"] == "send_only_participant":
        data["authorized_reader"] = input("Authorized reader label: ").strip()
    validate_config(data)
    print("Defaults: minimal_reference; registry writes require separate authorization.")
    return data


def write_config(root, data, replace=False):
    validate_config(data)
    local = Path(root) / "local"
    if local.is_symlink():
        raise ValueError("Refusing a symbolic-link local directory")
    local.mkdir(mode=0o700, exist_ok=True)
    path = local / "config.json"
    if path.is_symlink():
        raise ValueError("Refusing a symbolic-link configuration file")
    if path.exists() and not replace:
        raise ValueError("Local configuration already exists; use --replace to preserve a backup and change it")
    payload = (json.dumps(data, indent=2, ensure_ascii=True) + "\n").encode()
    backup = None
    if path.exists():
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = local / ("config.backup-" + stamp + "-" + uuid.uuid4().hex[:8] + ".json")
        fd = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(path.read_bytes())
    fd, temporary = tempfile.mkstemp(prefix=".config-", dir=str(local))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Read-only local integrity and configuration checks")
    configure = sub.add_parser("configure", help="Write local owner settings only")
    group = configure.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=Path)
    group.add_argument("--wizard", action="store_true")
    configure.add_argument("--replace", action="store_true", help="Preserve the existing config in a private backup")
    args = parser.parse_args()
    try:
        count = verify_bundle(SKILL_ROOT)
        if args.command == "doctor":
            path = SKILL_ROOT / "local/config.json"
            data = load_config(path) if path.exists() else dict(DEFAULT_CONFIG)
            report = settings_report(data)
            report["bundle_files_verified"] = count
            report["config_present"] = path.exists()
            print(json.dumps(report, indent=2))
            return 0 if report["configuration_state"] == "locally_complete" else 2
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
