from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.install_milestone3k_text import (candidate_targets as text_targets,
                                              install as install_text, rollback as rollback_text)
from src.extraction.garc import GARC

from milestone_installation_fixtures import recorded_candidate

ROOT = Path(__file__).resolve().parents[1]
TEXT_MANIFEST = ROOT / "build/milestone-3j/text-candidate/manifest.json"


def sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def modroot(profile: Path) -> Path:
    result = profile / "AzaharPlus/load/mods"
    result.mkdir(parents=True)
    return result


class Milestone3KTests(unittest.TestCase):
    def test_text_manifest_covers_exact_four_verified_precedence_targets(self):
        manifest, targets = text_targets(TEXT_MANIFEST)
        self.assertEqual(manifest["translation_records"], 227)
        self.assertEqual(len(targets), 4)
        self.assertEqual({row[1]["resource"] for row in targets}, {"a/0/7/4", "a/0/8/2"})
        for _relative, proof, path in targets:
            expected = "update-1.5" if proof["resource"] == "a/0/7/4" else "base"
            self.assertEqual(proof["source_version"], expected)
            raw = path.read_bytes()
            self.assertEqual(sha(raw), proof["output_sha256"])
            self.assertEqual(GARC.parse(raw).rebuild(), raw)

    def test_text_install_and_rollback_preserve_only_four_exact_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / "profile"
            mods = modroot(profile)
            targets = text_targets(TEXT_MANIFEST)[1]
            original = {}
            for index, (relative, _proof, _candidate) in enumerate(targets):
                path = mods.joinpath(*relative.split("/"))
                path.parent.mkdir(parents=True, exist_ok=True)
                original[relative] = f"prior-{index}".encode()
                path.write_bytes(original[relative])
            unrelated = mods / "0004000000055D00/romfs/unrelated.bin"
            unrelated.write_bytes(b"keep")
            record_root = root / "records"
            record = install_text(TEXT_MANIFEST, appdata=profile, record_root=record_root,
                                  prior_record_path=root / "no-prior-record.json")
            self.assertEqual(len(record["installed_files"]), 4)
            for row in record["installed_files"]:
                path = mods.joinpath(*row["relative_path"].split("/"))
                self.assertEqual(sha(path.read_bytes()), row["sha256"])
            self.assertEqual(unrelated.read_bytes(), b"keep")
            result = rollback_text(record_root=record_root, appdata=profile)
            self.assertTrue(result["rollback_verified"])
            for relative, data in original.items():
                self.assertEqual(mods.joinpath(*relative.split("/")).read_bytes(), data)
            self.assertEqual(unrelated.read_bytes(), b"keep")

    def test_text_installer_refuses_a_target_that_differs_from_3g_record(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / "profile"
            mods = modroot(profile)
            relative = "0004000000055D00/romfs/a/0/7/4"
            path = mods.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True)
            path.write_bytes(b"local modification")
            prior = root / "3g-record.json"
            prior.write_text(json.dumps({"milestone": "3G", "installed_files": [
                {"relative_path": relative, "installed_sha256": "0" * 64}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from its Milestone 3G hash"):
                install_text(TEXT_MANIFEST, appdata=profile, record_root=root / "records",
                             prior_record_path=prior)
            self.assertEqual(path.read_bytes(), b"local modification")

    def test_recorded_image_rollback_and_preserved_text_hashes(self):
        image_record_path = ROOT / "build/milestone-3k/image-install/rollback-record.json"
        self.assertTrue(image_record_path.is_file())
        image_record = json.loads(image_record_path.read_text(encoding="utf-8"))
        self.assertTrue(image_record["rollback_verified"])
        self.assertEqual(len(image_record["restored_paths"]), 2)
        old_install = json.loads((ROOT / "build/milestone-3k/image-install/installation-record.json")
                                 .read_text(encoding="utf-8"))
        self.assertTrue(all(not row["existed"] for row in old_install["backup_files"]))

        text_record = json.loads((ROOT / "build/milestone-3k/installation-record.json").read_text(encoding="utf-8"))
        root = ROOT / "build/milestone-3j/text-candidate"
        for record in text_record["installed_files"]:
            target = recorded_candidate(root, record)
            self.assertEqual(sha(target.read_bytes()), record["sha256"])
        self.assertTrue((ROOT / "build/milestone-3g/installation-record.json").is_file())
        self.assertFalse((ROOT / "build/milestone-3k/image-candidate").exists())
        self.assertFalse((ROOT / "build/milestone-3k/fight-artwork-test").exists())


if __name__ == "__main__":
    unittest.main()
