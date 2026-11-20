from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_milestone3k_fight_test import (CANONICAL, TEST_ROOT, build_candidate,
                                                 prepare_png, sha)
from scripts.install_milestone3k_image_test import (candidate_targets as image_targets,
                                                   install as install_image, rollback as rollback_image)
from scripts.install_milestone3k_text import (candidate_targets as text_targets,
                                              install as install_text, rollback as rollback_text)

ROOT = Path(__file__).resolve().parents[1]
TEXT_MANIFEST = ROOT / "build/milestone-3j/text-candidate/manifest.json"
IMAGE_MANIFEST = ROOT / "build/milestone-3k/image-candidate/manifest.json"


def modroot(profile: Path) -> Path:
    result = profile / "AzaharPlus/load/mods"
    result.mkdir(parents=True)
    return result


class Milestone3KTests(unittest.TestCase):
    def test_text_manifest_covers_exact_four_verified_update_precedence_targets(self):
        manifest, targets = text_targets(TEXT_MANIFEST)
        self.assertEqual(manifest["translation_records"], 227)
        self.assertEqual(len(targets), 4)
        self.assertEqual({row[1]["resource"] for row in targets}, {"a/0/7/4", "a/0/8/2"})
        for _relative, proof, path in targets:
            expected = "update-1.5" if proof["resource"] == "a/0/7/4" else "base"
            self.assertEqual(proof["source_version"], expected)
            self.assertEqual(sha(path.read_bytes()), proof["output_sha256"])

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

    def test_disposable_boi_png_and_image_candidate_leave_canonical_png_unchanged(self):
        canonical_hash = sha(CANONICAL.read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            test_root = Path(temp) / "art"
            metadata = prepare_png(test_root=test_root)
            (test_root / "manifest.json").write_text(json.dumps(metadata), encoding="utf-8")
            output = Path(temp) / "candidate"
            report = build_candidate(test_root=test_root, output_root=output)
            self.assertFalse(report["canonical_png_modified"])
            self.assertEqual(metadata["label"], "\u0411\u041e\u0419")
            self.assertEqual([row["dimensions"] for row in report["games"]], [[80, 50], [80, 50]])
        self.assertEqual(sha(CANONICAL.read_bytes()), canonical_hash)

    def test_image_candidate_installs_and_rolls_back_independently(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "candidate"
            image_report = build_candidate(TEST_ROOT, output)
            manifest_path = output / "manifest.json"
            self.assertEqual(len(image_targets(manifest_path)), 2)
            profile = root / "profile"
            mods = modroot(profile)
            originals = {}
            for index, (relative, _proof, _candidate) in enumerate(image_targets(manifest_path)):
                if index == 1:
                    continue
                path = mods.joinpath(*relative.split("/"))
                path.parent.mkdir(parents=True, exist_ok=True)
                original = b"prior-image-mod"
                path.write_bytes(original)
                originals[relative] = original
            unrelated = mods / "another-title/romfs/keep.bin"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_bytes(b"keep")
            records = root / "image-install"
            record = install_image(manifest_path, appdata=profile, record_root=records)
            self.assertEqual(len(record["installed_files"]), 2)
            self.assertFalse(record["backup_files"][1]["existed"])
            self.assertEqual(image_report["installed"], False)
            result = rollback_image(record_root=records, appdata=profile)
            self.assertTrue(result["rollback_verified"])
            for relative, data in originals.items():
                self.assertEqual(mods.joinpath(*relative.split("/")).read_bytes(), data)
            self.assertFalse(mods.joinpath(*image_targets(manifest_path)[1][0].split("/")).exists())
            self.assertEqual(unrelated.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
