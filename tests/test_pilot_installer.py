from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_gameplay_pilot.py"
SPEC = importlib.util.spec_from_file_location("pilot_installer", SCRIPT)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class PilotInstallerTests(unittest.TestCase):
    def test_install_records_existing_and_absent_targets_and_rollback_restores_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / "project" / "build" / "milestone-3c"
            appdata = root / "profile" / "AppData" / "Roaming"
            mod_root = appdata / "AzaharPlus" / "load" / "mods"
            old_x = b"previous X mod"
            old_y = b"previous Y mod"
            x_target = mod_root / "0004000000055D00/romfs/a/0/7/4"
            y_target = mod_root / "0004000000055E00/romfs/a/0/7/4"
            x_target.parent.mkdir(parents=True)
            y_target.parent.mkdir(parents=True)
            x_target.write_bytes(old_x)
            y_target.write_bytes(old_y)

            games = {}
            for game, title_id in (("pokemon-x", "0004000000055D00"), ("pokemon-y", "0004000000055E00")):
                resources = []
                for resource, payload, version in (
                    ("a/0/7/4", f"{game} options".encode(), "update-1.5"),
                    ("a/0/8/2", f"{game} dialogue".encode(), "base"),
                ):
                    rel_output = f"{game}/romfs/{resource}"
                    candidate = build / rel_output
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_bytes(payload)
                    resources.append({
                        "resource": resource,
                        "output_path": rel_output,
                        "output_sha256": hashlib.sha256(payload).hexdigest(),
                        "output_size": len(payload),
                        "source_version": version,
                    })
                games[game] = {"title_id": title_id, "resources": resources}
            build_manifest = {
                "milestone": "3C",
                "build_state": "unapproved_runtime_test_candidate",
                "games": games,
            }
            (build / "manifest.json").write_text(json.dumps(build_manifest), encoding="utf-8")
            backups = build / "installation-backups" / "test"
            record = build / "installation-record.json"

            with (
                patch.object(installer, "BUILD", build),
                patch.object(installer, "BUILD_MANIFEST", build / "manifest.json"),
                patch.object(installer, "BACKUP_ROOT", backups),
                patch.object(installer, "BACKUP_MANIFEST", backups / "manifest.json"),
                patch.object(installer, "INSTALL_RECORD", record),
                patch("os.environ", {"AZAHARPLUS_DATA_DIR": str(appdata / "AzaharPlus")}),
            ):
                installed = installer.install()
                saved = json.loads((backups / "manifest.json").read_text(encoding="utf-8"))
                states = {item["relative_path"]: item["existed"] for item in saved["files"]}
                self.assertEqual(states["0004000000055D00/romfs/a/0/7/4"], True)
                self.assertEqual(states["0004000000055D00/romfs/a/0/8/2"], False)
                self.assertEqual(len(installed["installed_files"]), 4)
                self.assertTrue((mod_root / "0004000000055D00/romfs/a/0/8/2").is_file())

                restored = installer.rollback()
                self.assertEqual(len(restored), 4)
                self.assertEqual(x_target.read_bytes(), old_x)
                self.assertEqual(y_target.read_bytes(), old_y)
                self.assertFalse((mod_root / "0004000000055D00/romfs/a/0/8/2").exists())
                self.assertFalse((mod_root / "0004000000055E00/romfs/a/0/8/2").exists())


if __name__ == "__main__":
    unittest.main()
