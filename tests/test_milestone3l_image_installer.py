from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.install_milestone3l_image import (EXPECTED_HASH, candidate_targets,
                                               install, rollback)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "build/milestone-3i/image-candidate/manifest.json"
IDS = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_tree(root: Path) -> tuple[Path, Path, dict[str, bytes], Path]:
    profile = root / "profile"
    mods = profile / "AzaharPlus/load/mods"
    mods.mkdir(parents=True)
    text_hashes = {}
    text_rows = []
    for title_id in IDS.values():
        for resource in ("a/0/7/4", "a/0/8/2"):
            relative = f"{title_id}/romfs/{resource}"
            path = mods.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("text:" + relative).encode())
            text_hashes[relative] = digest(path)
            text_rows.append({"relative_path": relative, "sha256": text_hashes[relative]})
    text_record = root / "text-record.json"
    text_record.write_text(json.dumps({"milestone": "3K", "build_milestone": "3J",
                                       "installed_files": text_rows}), encoding="utf-8")
    return profile, mods, text_hashes, text_record


class Milestone3LImageInstallerTests(unittest.TestCase):
    def test_manifest_selects_only_the_two_requested_image_archives(self):
        targets = candidate_targets(MANIFEST)
        self.assertEqual(len(targets), 2)
        self.assertEqual({row[1]["resource"] for row in targets}, {"a/2/4/0"})
        for _relative, proof, path in targets:
            self.assertEqual(proof["output_sha256"], EXPECTED_HASH)
            self.assertEqual(digest(path), EXPECTED_HASH)

    def test_install_and_rollback_preserve_text_unrelated_image_and_absent_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile, mods, text_before, text_record = setup_tree(root)
            image_targets = candidate_targets(MANIFEST)
            x_relative = image_targets[0][0]
            x_path = mods.joinpath(*x_relative.split("/"))
            x_path.parent.mkdir(parents=True, exist_ok=True)
            x_path.write_bytes(b"prior X image")
            prior_x = x_path.read_bytes()
            y_relative = image_targets[1][0]
            y_path = mods.joinpath(*y_relative.split("/"))
            other_image = mods / "0004000000055D00/romfs/a/2/3/9"
            other_image.parent.mkdir(parents=True, exist_ok=True)
            other_image.write_bytes(b"leave unchanged")

            records = root / "image-records"
            record = install(MANIFEST, appdata=profile, record_root=records,
                             text_record_path=text_record)
            self.assertEqual(len(record["installed_files"]), 2)
            self.assertTrue(record["backup_files"][0]["existed"])
            self.assertFalse(record["backup_files"][1]["existed"])
            self.assertEqual(digest(x_path), EXPECTED_HASH)
            self.assertEqual(digest(y_path), EXPECTED_HASH)
            self.assertEqual(other_image.read_bytes(), b"leave unchanged")
            for relative, expected in text_before.items():
                self.assertEqual(digest(mods.joinpath(*relative.split("/"))), expected)

            result = rollback(record_root=records, appdata=profile, text_record_path=text_record)
            self.assertTrue(result["rollback_verified"])
            self.assertEqual(x_path.read_bytes(), prior_x)
            self.assertFalse(y_path.exists())
            self.assertEqual(other_image.read_bytes(), b"leave unchanged")
            for relative, expected in text_before.items():
                self.assertEqual(digest(mods.joinpath(*relative.split("/"))), expected)

    def test_text_hash_mismatch_blocks_image_install_before_touching_image_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile, mods, _text_before, text_record = setup_tree(root)
            target = mods / "0004000000055D00/romfs/a/2/4/0"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"preexisting image")
            (mods / "0004000000055D00/romfs/a/0/7/4").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "Installed text archive changed"):
                install(MANIFEST, appdata=profile, record_root=root / "records",
                        text_record_path=text_record)
            self.assertEqual(target.read_bytes(), b"preexisting image")

    def test_wrong_candidate_hash_is_refused(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        target_row = next(row for row in manifest["games"]["pokemon-x"]["resources"]
                          if row["resource"] == "a/2/4/0")
        target_row["output_sha256"] = "0" * 64
        bad_manifest = MANIFEST.parent / "test-invalid-manifest.json"
        try:
            bad_manifest.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unexpected candidate hash"):
                candidate_targets(bad_manifest)
        finally:
            bad_manifest.unlink(missing_ok=True)

    def test_live_installation_record_contains_only_verified_image_targets(self):
        install_record = ROOT / "build/milestone-3m/installation/installation-record.json"
        self.assertTrue(install_record.is_file())
        record = json.loads(install_record.read_text(encoding="utf-8"))
        mods = Path(record["mod_root"])
        self.assertEqual(len(record["installed_files"]), 4)
        for row in record["installed_files"]:
            self.assertTrue(row["relative_path"].endswith(("/romfs/a/2/4/0", "/romfs/a/2/3/9")))
            self.assertEqual(digest(mods.joinpath(*row["relative_path"].split("/"))), row["sha256"])
        text_record = json.loads((ROOT / "build/milestone-3k/installation-record.json")
                                 .read_text(encoding="utf-8"))
        for row in text_record["installed_files"]:
            target = mods.joinpath(*row["relative_path"].split("/"))
            self.assertEqual(digest(target), row["sha256"])
        backup_manifest = json.loads(Path(record["backup_manifest"]).read_text(encoding="utf-8"))
        self.assertEqual({row["relative_path"] for row in backup_manifest["files"]},
                         {row["relative_path"] for row in record["installed_files"]})
        backup_rows = {row["relative_path"]: row for row in backup_manifest["files"]}
        self.assertEqual(len(backup_rows), 4)
        for relative, row in backup_rows.items():
            if relative.endswith("/a/2/4/0"):
                self.assertTrue(row["existed"])
                self.assertEqual(row["sha256"], EXPECTED_HASH)
            else:
                self.assertTrue(relative.endswith("/a/2/3/9"))
                self.assertFalse(row["existed"])


if __name__ == "__main__":
    unittest.main()
