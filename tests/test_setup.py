"""Exercise actual installer/config effects in temporary directories only."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills/agent-filing-protocol"
sys.path.insert(0, str(SOURCE / "scripts"))
import afp_setup as setup

spec = importlib.util.spec_from_file_location("afp_installer_test", ROOT / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def tree_hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def complete_config(role="preparer"):
    data = copy.deepcopy(setup.DEFAULT_CONFIG)
    data.update(owner_name="Example owner", ledger_email="ledger@example.invalid",
                agent_label="Muse (Example host)", role=role,
                authorized_matters=["DEMO-ROUND-1"], material_scope="Synthetic demo only",
                trusted_approval_channel="Owner's current authenticated chat",
                registry_location="owner chat only", responsible_filer="Muse (Example host)",
                retention_policy="Owner review after 30 days",
                sending_account="sender@example.invalid", readback_location="Authorized Sent view",
                authorized_reader="Dots (Example host)")
    return data


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="afp setup tests ")
        self.area = Path(self.temp.name)
        self.dest = self.area / "private workspace/skills/agent-filing-protocol"
        self.config = self.area / "owner.local.json"
        self.config.write_text(json.dumps(complete_config()))

    def tearDown(self):
        self.temp.cleanup()

    def run_installer(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "install.py"), "--target", "portable",
                               "--destination", str(self.dest), *args], cwd=str(self.area),
                              capture_output=True, text=True, timeout=15)

    def install(self, *args):
        result = self.run_installer(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def helper(self, *args):
        return subprocess.run([sys.executable, str(self.dest / "scripts/afp_setup.py"), *args],
                              cwd=str(self.area), capture_output=True, text=True, timeout=15)

    def test_dry_run_has_no_filesystem_effect(self):
        before = tree_hashes(self.area)
        report = self.install("--dry-run")
        self.assertEqual(report["action"], "dry_run")
        self.assertEqual(tree_hashes(self.area), before)
        self.assertFalse(self.dest.parent.exists())

    def test_default_hosts_install_in_isolated_home(self):
        for target, folder in (("codex", ".agents"), ("claude", ".claude")):
            with self.subTest(target=target), mock.patch.object(Path, "home", return_value=self.area), contextlib.redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(installer.main(["--target", target]), 0)
                report = json.loads(stream.getvalue())
                dest = self.area / folder / "skills/agent-filing-protocol"
                self.assertEqual(Path(report["destination"]), dest)
                self.assertTrue((dest / "SKILL.md").exists())
                self.assertGreater(setup.verify_bundle(dest), 5)

    def test_portable_install_from_unrelated_working_directory(self):
        report = self.install("--config", str(self.config))
        self.assertEqual(report["action"], "installed_locally")
        self.assertEqual(report["configuration_state"], "locally_complete")
        self.assertFalse(report["ready_to_send"])
        self.assertEqual(report["runtime_capabilities"], "not_observed")
        self.assertEqual(setup.load_config(self.dest / "local/config.json"), complete_config())
        self.assertEqual((self.dest / "references/PROTOCOL.md").read_bytes(), (ROOT / "PROTOCOL.md").read_bytes())

    def test_blank_settings_install_is_incomplete(self):
        report = self.install()
        self.assertEqual(report["configuration_state"], "incomplete")
        self.assertIn("authorized_matters", report["missing_fields"])
        self.assertEqual(setup.load_config(self.dest / "local/config.json")["authorized_matters"], [])
        result = self.helper("doctor")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(json.loads(result.stdout)["ready_to_send"])

    def test_doctor_is_read_only_and_never_certifies_mail(self):
        self.install("--config", str(self.config))
        before = tree_hashes(self.dest)
        result = self.helper("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["protocol_adoption"], "requires_trusted_owner_instruction")
        self.assertFalse(report["ready_to_send"])
        self.assertEqual(tree_hashes(self.dest), before)

    def test_repeated_install_preserves_settings_and_files(self):
        self.install("--config", str(self.config))
        before = tree_hashes(self.dest)
        self.assertEqual(self.install()["action"], "already_installed_unchanged")
        self.assertEqual(tree_hashes(self.dest), before)
        self.assertNotEqual(self.run_installer("--config", str(self.config)).returncode, 0)
        self.assertEqual(tree_hashes(self.dest), before)

    def test_existing_arbitrary_folder_is_preserved(self):
        self.dest.mkdir(parents=True)
        (self.dest / "keep.txt").write_text("Owner's existing work")
        before = tree_hashes(self.dest)
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual(tree_hashes(self.dest), before)

    def test_modified_installed_protocol_is_preserved_and_refused(self):
        self.install()
        (self.dest / "references/PROTOCOL.md").write_text("Changed protocol")
        before = tree_hashes(self.dest)
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual(tree_hashes(self.dest), before)
        self.assertEqual(self.helper("doctor").returncode, 1)

    def test_tampered_source_is_rejected_before_any_install(self):
        source_copy = self.area / "changed-source"
        shutil.copytree(SOURCE, source_copy)
        (source_copy / "references/PROTOCOL.md").write_text("Tampered")
        with mock.patch.object(installer, "SOURCE", source_copy), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(installer.main(["--destination", str(self.dest)]), 1)
        self.assertFalse(self.dest.parent.exists())

    def test_invalid_config_rejected_before_parent_creation(self):
        data = complete_config()
        data["oauth_token"] = "DO-NOT-STORE-SECRETS"
        self.config.write_text(json.dumps(data))
        self.assertNotEqual(self.run_installer("--config", str(self.config)).returncode, 0)
        self.assertFalse(self.dest.parent.exists())

    def test_config_replacement_requires_flag_and_preserves_backup(self):
        self.install("--config", str(self.config))
        old = (self.dest / "local/config.json").read_bytes()
        new = complete_config()
        new["agent_label"] = "Dots (Example host)"
        self.config.write_text(json.dumps(new))
        self.assertEqual(self.helper("configure", "--config", str(self.config)).returncode, 1)
        self.assertEqual((self.dest / "local/config.json").read_bytes(), old)
        result = self.helper("configure", "--config", str(self.config), "--replace")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.dest / "local").glob("config.backup-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), old)
        self.assertEqual(setup.load_config(self.dest / "local/config.json"), new)

    @unittest.skipIf(os.name == "nt", "POSIX mode check")
    def test_private_file_and_directory_modes(self):
        self.install()
        self.assertEqual(stat.S_IMODE((self.dest / "local").stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.dest / "local/config.json").stat().st_mode), 0o600)

    def test_duplicate_json_keys_are_rejected(self):
        self.config.write_text('{"config_version":1,"config_version":1}')
        with self.assertRaises(ValueError):
            setup.load_config(self.config)

    def test_invalid_settings_and_injection_boundaries(self):
        cases = [
            ("config_version", True), ("protocol_version", "AFP v99"),
            ("language_edition", "other"), ("role", "auto_sender"),
            ("agent_label", "Muse"), ("ledger_email", "a@example.invalid\r\nBcc: other@example.invalid"),
            ("ledger_email", "a@example.invalid,b@example.invalid"),
            ("authorized_matters", ["DEMO", "DEMO"]), ("authorized_matters", [False]),
            ("authorized_matters", [""]), ("registry_write_authorized", "true"),
            ("content_mode", "always_full"),
        ]
        for key, value in cases:
            with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                data = complete_config()
                data[key] = value
                setup.validate_config(data)

    def test_send_only_requires_reader_and_all_roles_stay_offline(self):
        for role in setup.ROLES:
            data = complete_config(role)
            report = setup.settings_report(data)
            self.assertEqual(report["configuration_state"], "locally_complete")
            self.assertFalse(report["ready_to_send"])
            self.assertEqual(report["runtime_capabilities"], "not_observed")
        data = complete_config("send_only_participant")
        data["authorized_reader"] = ""
        self.assertIn("authorized_reader", setup.settings_report(data)["missing_fields"])

    def test_symbolic_link_destination_cannot_redirect_install(self):
        self.dest.parent.mkdir(parents=True)
        outside = self.area / "outside"
        outside.mkdir()
        (outside / "keep").write_text("Do not alter")
        self.dest.symlink_to(outside, target_is_directory=True)
        before = tree_hashes(outside)
        self.assertEqual(self.run_installer().returncode, 1)
        self.assertEqual(tree_hashes(outside), before)

    def test_source_symbolic_link_is_refused(self):
        source_copy = self.area / "linked-source"
        shutil.copytree(SOURCE, source_copy)
        (source_copy / "extra").symlink_to(self.config)
        with self.assertRaises(ValueError):
            setup.verify_bundle(source_copy)

    def test_existing_install_lock_is_not_removed(self):
        self.dest.parent.mkdir(parents=True)
        lock = self.dest.parent / ".agent-filing-protocol.install.lock"
        lock.write_text("Another run owns this")
        self.assertEqual(self.run_installer().returncode, 1)
        self.assertEqual(lock.read_text(), "Another run owns this")
        self.assertFalse(self.dest.exists())

    def test_bad_destination_name_and_portable_missing_destination(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(installer.main(["--target", "portable"]), 1)
            self.assertEqual(installer.main(["--destination", str(self.area / "wrong-folder")]), 1)
        self.assertFalse((self.area / "wrong-folder").exists())

    def test_noninteractive_wizard_fails_without_writes(self):
        result = subprocess.run([sys.executable, str(ROOT / "install.py"), "--destination", str(self.dest), "--wizard"],
                                input="", capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.dest.parent.exists())

    def test_json_output_does_not_echo_private_settings(self):
        self.install("--config", str(self.config))
        result = self.helper("doctor")
        self.assertNotIn("ledger@example.invalid", result.stdout)
        self.assertNotIn("Owner's current authenticated chat", result.stdout)

    def test_local_symlink_prevents_configuration_write(self):
        self.install()
        config = self.dest / "local/config.json"
        config.unlink()
        config.symlink_to(self.config)
        before = self.config.read_bytes()
        self.assertEqual(self.helper("configure", "--config", str(self.config), "--replace").returncode, 1)
        self.assertEqual(self.config.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
