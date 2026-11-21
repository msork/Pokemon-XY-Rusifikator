from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.install_milestone3m_images import candidate_targets, install, rollback

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "build/milestone-3m/candidate/milestone-3m-manifest.json"
TEXT_RECORD = ROOT / "build/milestone-3k/installation-record.json"
HASHES = {
    "a/2/4/0": "ea90b16d693df77b86d935383207d9a02bcd6728534999be0f59d80464d1a9a0",
    "a/2/3/9": "5f1f1ee312ee793417ad9808c733649791e9cb2e56ab5279bd66b44297399226",
}
IDS = ("0004000000055D00", "0004000000055E00")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root: Path) -> tuple[Path, Path]:
    profile = root / "profile"
    mods = profile / "AzaharPlus/load/mods"
    mods.mkdir(parents=True)
    rows = []
    for title_id in IDS:
        for resource in ("a/0/7/4", "a/0/8/2"):
            relative = f"{title_id}/romfs/{resource}"
            path = mods.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
            rows.append({"relative_path": relative, "sha256": digest(path)})
    text_record = root / "text-record.json"
    text_record.write_text(json.dumps({"milestone": "3K", "build_milestone": "3J",
                                       "installed_files": rows}), encoding="utf-8")
    return profile, text_record


class Milestone3MTests(unittest.TestCase):
    def test_candidate_hashes_and_scope(self):
        targets = candidate_targets(MANIFEST)
        self.assertEqual(len(targets), 4)
        for _relative, proof, path in targets:
            self.assertEqual(proof["output_sha256"], HASHES[proof["resource"]])
            self.assertEqual(digest(path), HASHES[proof["resource"]])

    def test_install_rollback_preserves_text_unrelated_files_and_absent_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile, text_record = fixture(root)
            mods = profile / "AzaharPlus/load/mods"
            targets = candidate_targets(MANIFEST)
            existing_rel = targets[0][0]
            existing = mods.joinpath(*existing_rel.split("/"))
            existing.parent.mkdir(parents=True, exist_ok=True)
            existing.write_bytes(b"prior image")
            unrelated = mods / IDS[0] / "romfs/other-mod.bin"
            unrelated.write_bytes(b"keep this")
            text_hashes = {row["relative_path"]: row["sha256"]
                           for row in json.loads(text_record.read_text())["installed_files"]}
            records = root / "records"
            record = install(MANIFEST, appdata=profile, record_root=records,
                             text_record_path=text_record)
            self.assertEqual(len(record["installed_files"]), 4)
            self.assertTrue(any(row["existed"] for row in record["backup_files"]))
            self.assertTrue(any(not row["existed"] for row in record["backup_files"]))
            for relative, proof, _source in targets:
                self.assertEqual(digest(mods.joinpath(*relative.split("/"))), HASHES[proof["resource"]])
            self.assertEqual(unrelated.read_bytes(), b"keep this")
            for relative, expected in text_hashes.items():
                self.assertEqual(digest(mods.joinpath(*relative.split("/"))), expected)
            result = rollback(record_root=records, appdata=profile, text_record_path=text_record)
            self.assertTrue(result["rollback_verified"])
            self.assertEqual(existing.read_bytes(), b"prior image")
            self.assertFalse(mods.joinpath(*targets[1][0].split("/")).exists())
            self.assertEqual(unrelated.read_bytes(), b"keep this")
            for relative, expected in text_hashes.items():
                self.assertEqual(digest(mods.joinpath(*relative.split("/"))), expected)

    def test_invalid_candidate_hash_stops_before_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile, text_record = fixture(root)
            data = json.loads(MANIFEST.read_text(encoding="utf-8"))
            candidate_root = root / "candidate"
            candidate_root.mkdir()
            for game_data in data["games"].values():
                for row in game_data["resources"]:
                    source = MANIFEST.parent / row["output_path"]
                    destination = candidate_root / row["output_path"]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read_bytes())
            data["games"]["pokemon-x"]["resources"][0]["output_sha256"] = "0" * 64
            bad = candidate_root / "milestone-3m-manifest.json"
            bad.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                install(bad, appdata=profile, record_root=root / "records", text_record_path=text_record)
            self.assertFalse((profile / "AzaharPlus/load/mods/0004000000055D00/romfs/a/2/4/0").exists())

    def test_live_installation_record_and_milestone_3k_text_hashes(self):
        install_record_path = ROOT / "build/milestone-3m/installation/installation-record.json"
        self.assertTrue(install_record_path.is_file())
        record = json.loads(install_record_path.read_text(encoding="utf-8"))
        mods = Path(record["mod_root"])
        self.assertEqual(len(record["installed_files"]), 4)
        for row in record["installed_files"]:
            self.assertEqual(digest(mods.joinpath(*row["relative_path"].split("/"))), row["sha256"])
            self.assertEqual(row["sha256"], HASHES[row["resource"]])
        for row in record["text_files_verified_unchanged"]:
            self.assertEqual(digest(mods.joinpath(*row["relative_path"].split("/"))), row["sha256"])


if __name__ == "__main__":
    unittest.main()
