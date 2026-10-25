"""Synthetic regression and fault-injection tests; never use a real host install."""
import contextlib
import copy
import errno
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
from test_setup import ROOT, SOURCE, complete_config, installer, setup, tree_hashes


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="afp-hardening-")
        self.area = Path(self.temp.name)
        self.dest = self.area / "skills/agent-filing-protocol"

    def tearDown(self):
        self.temp.cleanup()

    def test_sender_and_ledger_are_distinct_in_all_four_copies(self):
        data = complete_config()
        self.assertNotEqual(data["sending_account"], data["ledger_email"])
        for relative in ("templates/filing-email.md", "examples/example-filing.md",
                         "skills/agent-filing-protocol/assets/filing-email.md",
                         "skills/agent-filing-protocol/references/example-filing.md"):
            text = (ROOT / relative).read_text()
            self.assertIn("From: <SENDING_ACCOUNT>\nTo: <LEDGER_EMAIL>", text)

    def test_first_creation_publishes_only_fully_written_bytes(self):
        self.dest.mkdir(parents=True)
        real_link = os.link
        observed = []
        def link(source, destination):
            observed.append(json.loads(Path(source).read_text()))
            self.assertFalse(Path(destination).exists())
            return real_link(source, destination)
        with mock.patch.object(setup.os, "link", side_effect=link):
            setup.write_config(self.dest, complete_config())
        self.assertEqual(observed, [complete_config()])
        self.assertEqual(setup.load_config(self.dest / "local/config.json"), complete_config())

    def test_failure_before_publication_leaves_no_partial_config(self):
        self.dest.mkdir(parents=True)
        with mock.patch.object(setup.os, "fsync", side_effect=OSError("Synthetic fsync failure")):
            with self.assertRaises(OSError):
                setup.write_config(self.dest, complete_config())
        self.assertFalse((self.dest / "local/config.json").exists())
        self.assertEqual(list((self.dest / "local").iterdir()), [])

    def test_concurrent_creator_is_never_overwritten(self):
        self.dest.mkdir(parents=True)
        real_link = os.link
        other = copy.deepcopy(complete_config())
        other["agent_label"] = "Dots (Example host)"
        def collide(source, destination):
            fd = os.open(str(destination), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as stream:
                json.dump(other, stream)
            return real_link(source, destination)
        with mock.patch.object(setup.os, "link", side_effect=collide), self.assertRaises(ValueError):
            setup.write_config(self.dest, complete_config())
        self.assertEqual(setup.load_config(self.dest / "local/config.json"), other)

    def test_unsupported_atomic_creation_fails_without_a_final_file(self):
        self.dest.mkdir(parents=True)
        with mock.patch.object(setup.os, "link", side_effect=OSError(errno.EPERM, "Synthetic unsupported link")):
            with self.assertRaisesRegex(OSError, "hard-link support"):
                setup.write_config(self.dest, complete_config())
        self.assertFalse((self.dest / "local/config.json").exists())

    def test_process_exit_after_publication_retains_complete_config(self):
        self.dest.mkdir(parents=True)
        code = '''import importlib.util,os,pathlib,sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location("fixture_setup",sys.argv[1])
setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
real=os.link
def publish_then_exit(source,destination):
    real(source,destination);os._exit(93)
setup.os.link=publish_then_exit
setup.write_config(pathlib.Path(sys.argv[2]),dict(setup.DEFAULT_CONFIG))
'''
        result = subprocess.run([sys.executable, "-I", "-c", code, str(SOURCE / "scripts/afp_setup.py"), str(self.dest)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 93)
        self.assertEqual(setup.load_config(self.dest / "local/config.json"), setup.DEFAULT_CONFIG)

    def test_replace_failure_preserves_original_and_complete_backup(self):
        self.dest.mkdir(parents=True)
        setup.write_config(self.dest, complete_config())
        old = (self.dest / "local/config.json").read_bytes()
        with mock.patch.object(setup.os, "replace", side_effect=OSError("Synthetic replace failure")):
            with self.assertRaises(OSError):
                setup.write_config(self.dest, dict(setup.DEFAULT_CONFIG), replace=True)
        self.assertEqual((self.dest / "local/config.json").read_bytes(), old)
        backups = list((self.dest / "local").glob("config.backup-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), old)

    @unittest.skipUnless(os.name == "posix", "POSIX permission check")
    def test_existing_unsafe_directory_is_rejected_without_chmod(self):
        local = self.dest / "local"
        local.mkdir(parents=True)
        local.chmod(0o777)
        with self.assertRaisesRegex(ValueError, "owner-only"):
            setup.write_config(self.dest, complete_config())
        self.assertEqual(local.stat().st_mode & 0o777, 0o777)
        self.assertFalse((local / "config.json").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX permission check")
    def test_doctor_rejects_unsafe_directory_and_config_file(self):
        shutil.copytree(SOURCE, self.dest)
        setup.write_config(self.dest, complete_config())
        for path, mode in [(self.dest / "local", 0o777), (self.dest / "local/config.json", 0o644)]:
            old = path.stat().st_mode & 0o777
            path.chmod(mode)
            result = subprocess.run([sys.executable, "-I", str(self.dest / "scripts/afp_setup.py"), "doctor"],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertIn("owner-only", result.stderr)
            self.assertEqual(path.stat().st_mode & 0o777, mode)
            path.chmod(old)

    def test_oversized_generated_config_is_refused_before_mkdir(self):
        data = complete_config()
        data["authorized_matters"] = [str(i) + "x" * 500 for i in range(180)]
        with self.assertRaisesRegex(ValueError, "64 KiB"):
            setup.write_config(self.dest, data)
        self.assertFalse(self.dest.exists())

    def test_stdin_limits_utf8_duplicate_keys_and_malformed_json(self):
        payload = json.dumps(complete_config())
        for value, valid in [(payload.ljust(65536), True), (payload.ljust(65537), False),
                             (payload + " " * 65000 + "汉" * 300, False),
                             ('{"config_version":1,"config_version":1}', False), ("{", False)]:
            with self.subTest(valid=valid), mock.patch.object(setup.sys, "stdin", io.StringIO(value)):
                if valid:
                    self.assertEqual(setup.load_config("-"), complete_config())
                else:
                    with self.assertRaises(ValueError):
                        setup.load_config("-")
        international = complete_config()
        international["owner_name"] = "Synthetic O'Name 汉"
        stream = io.TextIOWrapper(io.BytesIO(json.dumps(international, ensure_ascii=False).encode("utf-8")), encoding="ascii")
        with mock.patch.object(setup.sys, "stdin", stream):
            self.assertEqual(setup.load_config("-"), international)

    def test_metadata_named_symlinks_and_pycache_are_rejected(self):
        shutil.copytree(SOURCE, self.dest)
        if os.name != "nt":
            link = self.dest / ".DS_Store"
            link.symlink_to(self.dest / "SKILL.md")
            with self.assertRaises(ValueError):
                setup.verify_bundle(self.dest)
            link.unlink()
        cache = self.dest / "__pycache__"
        cache.mkdir()
        (cache / "fixture.pyc").write_bytes(b"not executable bytecode")
        with self.assertRaisesRegex(ValueError, "unexpected"):
            setup.verify_bundle(self.dest)

    def test_existing_install_is_refused_before_wizard(self):
        shutil.copytree(SOURCE, self.dest)
        with mock.patch.object(installer, "wizard") as wizard, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(installer.main(["--destination", str(self.dest), "--wizard"]), 1)
        wizard.assert_not_called()

    def test_different_version_remains_refused_and_unchanged(self):
        shutil.copytree(SOURCE, self.dest)
        (self.dest / "SKILL.md").write_text("Synthetic other version")
        manifest = {p.relative_to(self.dest).as_posix(): __import__("hashlib").sha256(p.read_bytes()).hexdigest()
                    for p in self.dest.rglob("*") if p.is_file() and p.name != "MANIFEST.json"}
        (self.dest / "MANIFEST.json").write_text(json.dumps(manifest))
        before = tree_hashes(self.dest)
        with contextlib.redirect_stderr(io.StringIO()), mock.patch.object(installer, "wizard") as wizard:
            self.assertEqual(installer.main(["--destination", str(self.dest), "--wizard"]), 1)
        wizard.assert_not_called()
        self.assertEqual(tree_hashes(self.dest), before)

    def test_cleanup_failure_does_not_skip_owned_lock_release(self):
        real_rename = Path.rename
        def fail_stage(path, target):
            if path.name.startswith(".afp-stage-"):
                raise OSError("Synthetic publication failure")
            return real_rename(path, target)
        with mock.patch.object(Path, "rename", fail_stage), \
                mock.patch.object(installer.shutil, "rmtree", side_effect=PermissionError("Synthetic cleanup failure")), \
                contextlib.redirect_stderr(io.StringIO()) as log:
            self.assertEqual(installer.main(["--destination", str(self.dest)]), 1)
        self.assertIn("publication failure", log.getvalue())
        self.assertIn("cleanup incomplete", log.getvalue())
        self.assertFalse((self.dest.parent / ".agent-filing-protocol.install.lock").exists())
        self.assertFalse(self.dest.exists())

    def test_minimum_version_guard_runs_before_setup(self):
        code = 'import runpy,sys;sys.version_info=(3,8,0);runpy.run_path(sys.argv[1],run_name="__main__")'
        for file in [ROOT / "install.py", SOURCE / "scripts/afp_setup.py"]:
            result = subprocess.run([sys.executable, "-I", "-c", code, str(file)], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Python 3.9", result.stderr)

    @unittest.skipUnless(os.name == "posix", "Real POSIX terminal")
    def test_real_terminal_retries_and_preserves_earlier_answers(self):
        import pty
        import select
        import time
        master, slave = pty.openpty()
        proc = subprocess.Popen([sys.executable, "-I", str(ROOT / "install.py"), "--destination", str(self.dest), "--wizard"],
                                stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        chunks = []
        try:
            answers = ["Synthetic owner", "bad-email", "ledger@example.invalid", "Muse (Example host)",
                       "auditor", "preparer", "SYNTHETIC", "Synthetic materials", "Synthetic owner channel",
                       "owner chat only", "Muse (Example host)", "30 days"]
            os.write(master, ("\n".join(answers) + "\n").encode())
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], 0.1)
                if ready:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                if proc.poll() is not None and not ready:
                    break
            self.assertEqual(proc.wait(timeout=2), 0)
        finally:
            if proc.poll() is None:
                proc.kill(); proc.wait(timeout=2)
            os.close(master)
        self.assertEqual(b"".join(chunks).decode().count("Please enter it again."), 2)
        self.assertEqual(setup.load_config(self.dest / "local/config.json")["owner_name"], "Synthetic owner")


if __name__ == "__main__":
    unittest.main()
