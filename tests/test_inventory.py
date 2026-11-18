import tempfile
import unittest
from pathlib import Path

from scripts.inventory import compare, inventory, write_manifest


class InventoryTests(unittest.TestCase):
    def test_inventory_is_deterministic_and_hashes_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "b").write_bytes(b"same")
            (root / "nested").mkdir()
            (root / "nested" / "a").write_bytes(b"changed")
            rows = inventory(root)
            self.assertEqual([r["path"] for r in rows], ["b", "nested/a"])
            self.assertEqual(len(rows[0]["sha256"]), 64)
            output = Path(directory).parent / (Path(directory).name + "-manifest.jsonl")
            self.assertEqual(write_manifest(root, output), inventory(root))

    def test_compare_classifies_path_and_content_differences(self):
        left = [{"path": "same", "sha256": "a"}, {"path": "diff", "sha256": "b"}, {"path": "left", "sha256": "c"}]
        right = [{"path": "same", "sha256": "a"}, {"path": "diff", "sha256": "x"}, {"path": "right", "sha256": "d"}]
        self.assertEqual(compare(left, right), {"identical": ["same"], "different": ["diff"], "left_only": ["left"], "right_only": ["right"]})


if __name__ == "__main__":
    unittest.main()
