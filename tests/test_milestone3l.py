from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_milestone3l_fight_reference import SOURCE, build
from src.rebuilding.textures import read_png_rgba

ROOT = Path(__file__).resolve().parents[1]


class Milestone3LTests(unittest.TestCase):
    def test_native_copy_and_nearest_neighbor_preview_preserve_original_pixels(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "references"
            report = build(output)
            native = output / "fight_text-original-80x50.png"
            enlarged = output / "fight_text-nearest-8x-640x400.png"
            self.assertEqual(native.read_bytes(), SOURCE.read_bytes())
            self.assertEqual(read_png_rgba(native)[:2], (80, 50))
            self.assertEqual(read_png_rgba(enlarged)[:2], (640, 400))
            _w, _h, original = read_png_rgba(native)
            _w, _h, scaled = read_png_rgba(enlarged)
            for y in range(50):
                for x in range(80):
                    pixel = original[(y * 80 + x) * 4:(y * 80 + x + 1) * 4]
                    for dy in range(8):
                        start = (((y * 8 + dy) * 640) + x * 8) * 4
                        self.assertEqual(scaled[start:start + 32], pixel * 8)
            self.assertTrue(report["pixels_verified"])
            self.assertFalse(report["replacement_art_created"])
            self.assertFalse(report["source_image_modified"])

    def test_original_style_measurements_and_review_status_are_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "references"
            report = build(output)
            self.assertEqual(report["source_sha256"], "c3317a191a48b540b0e3b87e35baed574d4d47f0bf4171c5beeb0d95280646b9")
            analysis = report["source_image_analysis"]
            self.assertEqual(analysis["alpha_nonzero_bbox_xyxy"], [4, 15, 77, 35])
            self.assertEqual(analysis["red_ink_bbox_xyxy"], [8, 18, 75, 32])
            self.assertEqual(analysis["transparent_pixel_count"], 2669)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["replacement_art_created"])
            self.assertEqual(manifest["native_sha256"], manifest["source_sha256"])

    def test_rejected_milestone3k_image_is_absent_and_text_install_remains_valid(self):
        mods = Path.home() / "AppData/Roaming/AzaharPlus/load/mods"
        rollback = json.loads((ROOT / "build/milestone-3k/image-install/rollback-record.json")
                              .read_text(encoding="utf-8"))
        self.assertTrue(rollback["rollback_verified"])
        for relative in rollback["restored_paths"]:
            self.assertFalse(mods.joinpath(*relative.split("/")).exists())
        text_record = json.loads((ROOT / "build/milestone-3k/installation-record.json")
                                 .read_text(encoding="utf-8"))
        import hashlib
        for row in text_record["installed_files"]:
            target = mods.joinpath(*row["relative_path"].split("/"))
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row["sha256"])


if __name__ == "__main__":
    unittest.main()
