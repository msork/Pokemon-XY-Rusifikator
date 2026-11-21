from __future__ import annotations

import struct
import unittest

from scripts.scan_milestone3n_artwork import _bclim_at_end, category_for


class Milestone3NScanTests(unittest.TestCase):
    def test_visual_review_categories_use_resource_and_filename_context(self):
        self.assertEqual(category_for("a/0/1/9", "strinput_bg.bclim"), "keyboard")
        self.assertEqual(category_for("a/2/4/0", "fight_text.bclim"), "battle")
        self.assertEqual(category_for("a/7/4/1", "unknown.bclim"), "unclassified_manual_review")

    def test_standalone_bclim_requires_footer_at_file_end_and_matching_payload_length(self):
        prefix = b"pixels"
        footer = bytearray(40)
        footer[:4] = b"CLIM"
        struct.pack_into("<I", footer, 36, len(prefix))
        raw = prefix + footer
        self.assertEqual(_bclim_at_end(raw), raw)
        self.assertIsNone(_bclim_at_end(raw + b"tail"))
        struct.pack_into("<I", footer, 36, len(prefix) + 1)
        self.assertIsNone(_bclim_at_end(prefix + footer))


if __name__ == "__main__":
    unittest.main()
