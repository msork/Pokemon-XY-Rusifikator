from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_milestone3l_fight_reference import SOURCE, build
from src.rebuilding.textures import read_png_rgba

from milestone_installation_fixtures import recorded_candidate

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
            self.assertEqual(report["source_sha256"], hashlib.sha256(SOURCE.read_bytes()).hexdigest())
            analysis = report["source_image_analysis"]
            self.assertIsNotNone(analysis["alpha_nonzero_bbox_xyxy"])
            self.assertIsNotNone(analysis["red_ink_bbox_xyxy"])
            self.assertGreater(analysis["transparent_pixel_count"], 0)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["replacement_art_created"])
            self.assertEqual(manifest["native_sha256"], manifest["source_sha256"])

    def test_recorded_image_rollback_and_text_candidate_hashes(self):
        rollback = json.loads((ROOT / "build/milestone-3k/image-install/rollback-record.json")
                              .read_text(encoding="utf-8"))
        self.assertTrue(rollback["rollback_verified"])
        old_image_install = json.loads((ROOT / "build/milestone-3k/image-install/installation-record.json")
                                       .read_text(encoding="utf-8"))
        self.assertTrue(all(not row["existed"] for row in old_image_install["backup_files"]))
        self.assertEqual(len(rollback["restored_paths"]), 2)
        text_candidate = ROOT / "build/milestone-3j/text-candidate"
        text_record = json.loads((ROOT / "build/milestone-3k/installation-record.json")
                                 .read_text(encoding="utf-8"))
        for row in text_record["installed_files"]:
            target = recorded_candidate(text_candidate, row)
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), row["sha256"])


if __name__ == "__main__":
    unittest.main()
