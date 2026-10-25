"""Adversarial controls for the public validator and archive builder."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_release as release
from sync_skill import synchronize


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agentlogue-release-tests-")
        self.area = Path(self.temp.name)
        self.root = self.area / "source"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def tearDown(self):
        self.temp.cleanup()

    def test_canonical_protocol_bytes_remain_pinned(self):
        self.assertEqual(hashlib.sha256((ROOT / "PROTOCOL.md").read_bytes()).hexdigest(),
                         "207b008a244130446ccdee2fd8fadabbd55aeb40056778e3f960bae5649bf06d")

    def test_schema_example_and_four_negative_controls(self):
        self.assertEqual(release.schema_checks(self.root)["negative_controls_rejected"], 4)

    def test_changed_resource_is_detected(self):
        (self.root / "skills/agent-filing-protocol/references/PROTOCOL.md").write_text("Synthetic change")
        with self.assertRaises(ValueError):
            release.check_source(self.root)

    def test_internally_consistent_wrong_sender_is_detected(self):
        for path in ["templates/filing-email.md", "examples/example-filing.md"]:
            file = self.root / path
            file.write_text(file.read_text().replace("<SENDING_ACCOUNT>", "<LEDGER_EMAIL>"))
        synchronize(self.root)
        with self.assertRaisesRegex(ValueError, "Sender"):
            release.check_source(self.root)

    def test_stale_version_marker_is_detected(self):
        file = self.root / "README.md"
        file.write_text(file.read_text().replace("v1.4.3-en", "v1.4.2-en"))
        with self.assertRaisesRegex(ValueError, "version"):
            release.check_source(self.root)

    def test_version_cannot_escape_archive_output(self):
        original, _ = release.check_source(self.root)
        file = self.root / "release.json"
        data = json.loads(file.read_text())
        data["version"] = "../../outside"
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "version"):
            release.check_source(self.root)
        with self.assertRaisesRegex(ValueError, "version"):
            release.build_archives(self.root, self.area / "invalid-output", original["inventory"])
        self.assertFalse((self.area / "invalid-output").exists())

    def test_private_local_data_is_never_bundled(self):
        local = self.root / "skills/agent-filing-protocol/local"
        local.mkdir()
        (local / "config.json").write_text("{}")
        with self.assertRaises(ValueError):
            release.public_files(self.root)

    def test_embedded_repository_metadata_is_rejected(self):
        embedded = self.root / "scripts/.git"
        embedded.mkdir()
        (embedded / "config").write_text("Synthetic repository metadata")
        with self.assertRaises(ValueError):
            release.public_files(self.root)

    def test_metadata_exclusion_is_consistent_and_directories_cannot_hide(self):
        file = self.root / "skills/agent-filing-protocol/.DS_Store"
        file.write_bytes(b"Synthetic metadata")
        synchronize(self.root, check=True)
        source, _ = release.check_source(self.root)
        self.assertFalse(any(row["path"].endswith(".DS_Store") for row in source["inventory"]))
        file.unlink()
        file.mkdir()
        (file / "payload.txt").write_text("Synthetic")
        with self.assertRaises(ValueError):
            release.check_source(self.root)

    def test_privacy_and_media_negative_controls(self):
        with self.assertRaises(ValueError):
            release.check_text("owner" + "@" + "example.com", "fixture")
        with self.assertRaises(ValueError):
            release.check_text("/Users/" + "synthetic-owner" + "/private", "fixture")
        data = (self.root / "assets/agent-conversation-map.png").read_bytes()
        with self.assertRaises(ValueError):
            release.inspect_png(data + b"synthetic trailing bytes")

    def test_archives_are_repeatable_and_reject_source_change(self):
        source, _ = release.check_source(self.root)
        first = release.build_archives(self.root, self.area / "first", source["inventory"])
        second = release.build_archives(self.root, self.area / "second", source["inventory"])
        self.assertEqual(first, second)
        file = self.root / "README.md"
        file.write_text(file.read_text() + "\nSynthetic change.\n")
        with self.assertRaisesRegex(ValueError, "changed during build"):
            release.build_archives(self.root, self.area / "changed", source["inventory"])


if __name__ == "__main__":
    unittest.main()
