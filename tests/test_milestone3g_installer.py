from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_milestone3g.py"
SPEC = importlib.util.spec_from_file_location("milestone3g_installer", SCRIPT)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Milestone3GInstallerTests(unittest.TestCase):
    def fixture(self, root: Path):
        profile = root / "profile" / "AppData" / "Roaming"
        mod_root = profile / "AzaharPlus" / "load" / "mods"
        build_root = root / "build" / "milestone-3g" / "candidate"
        record_root = root / "build" / "milestone-3g"
        games = {}
        for game, title_id in installer.GAMES.items():
            resources = []
            for resource in installer.EXPECTED_RESOURCES:
                payload = f"candidate:{game}:{resource}".encode()
                relative_output = f"{game}/romfs/{resource}"
                candidate = build_root / relative_output
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_bytes(payload)
                resources.append({
                    "resource": resource,
                    "source_version": installer.EXPECTED_RESOURCES[resource],
                    "output_path": relative_output,
                    "output_size": len(payload),
                    "output_sha256": digest(payload),
                })
            games[game] = {"title_id": title_id, "resources": resources}
        manifest = {
            "milestone": "3G",
            "build_state": "unapproved_runtime_test_candidate",
            "runtime_tested": False,
            "installed": False,
            "original_assets_modified": False,
            "games": games,
        }
        manifest_path = build_root / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return profile, mod_root, build_root, record_root, manifest_path

    def test_install_and_rollback_restore_existing_and_absent_targets_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile, mod_root, _, record_root, manifest_path = self.fixture(root)
            mod_root.mkdir(parents=True, exist_ok=True)
            relatives = [f"{title}/romfs/{resource}" for title in installer.GAMES.values()
                         for resource in installer.EXPECTED_RESOURCES]
            original = {}
            for index, relative in enumerate(relatives):
                target = mod_root.joinpath(*relative.split("/"))
                if index != 2:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(f"prior:{relative}".encode())
                    original[relative] = target.read_bytes()
                else:
                    original[relative] = None
            unrelated = mod_root / "unrelated-mod" / "romfs" / "keep.bin"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_bytes(b"unrelated")

            record = installer.install(manifest_path, profile, record_root)
            backup_rows = {row["relative_path"]: row for row in record["backup_files"]}
            self.assertEqual(len(record["installed_files"]), 4)
            for row in record["installed_files"]:
                target = mod_root.joinpath(*row["relative_path"].split("/"))
                self.assertEqual(installer.sha256(target), row["installed_sha256"])
                self.assertEqual(backup_rows[row["relative_path"]]["existed"],
                                 original[row["relative_path"]] is not None)

            result = installer.rollback(record_root, profile)
            self.assertTrue(result["rollback_verified"])
            for relative, data in original.items():
                target = mod_root.joinpath(*relative.split("/"))
                if data is None:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), data)
            self.assertEqual(unrelated.read_bytes(), b"unrelated")

    def test_bad_candidate_hash_fails_before_touching_mod_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile, mod_root, build_root, record_root, manifest_path = self.fixture(root)
            candidate = build_root / "pokemon-x" / "romfs" / "a" / "0" / "7" / "4"
            candidate.write_bytes(b"damaged")
            with self.assertRaisesRegex(ValueError, "Candidate size differs|Candidate hash differs"):
                installer.install(manifest_path, profile, record_root)
            self.assertFalse(mod_root.exists())
            self.assertFalse((record_root / "installation-backups").exists())


if __name__ == "__main__":
    unittest.main()
