import json
import struct
import tempfile
import unittest
from pathlib import Path

from scripts.extract_milestone3h_textures import _png_chunk, write_png
from scripts.build_milestone3i_text_candidate import build_text_candidate, rollback_text_candidate
from scripts.build_milestone3i_textures import (EXPECTED_PNGS, build_images, initialize_editing_workspace)
from src.extraction.garc import GARC
from src.extraction.lz11 import decompress
from src.extraction.messages import TextFile
from src.rebuilding.textures import (backup_workspace, decode_bclim, encode_bclim, lz11_literal_compress,
                                     read_png_rgba, restore_workspace)
from scripts.build_milestone3i_textures import restore_candidate

ROOT = Path(__file__).resolve().parents[1]


class Milestone3ITests(unittest.TestCase):
    def test_all_24_original_pngs_reencode_byte_exact_and_garc_dry_run_is_identical(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            editing = root / "editing"
            initialize_editing_workspace(editing)
            manifest = json.loads((editing / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["assets"]), 24)
            self.assertEqual({path.name for path in editing.glob("*.png")}, EXPECTED_PNGS)
            result = build_images(editing_root=editing, output_root=root / "dry-run", dry_run=True)
            self.assertEqual(set(result["games"]), {"pokemon-x", "pokemon-y"})
            for game in result["games"].values():
                self.assertEqual(len(game["resources"]), 2)
                for resource in game["resources"]:
                    self.assertTrue(resource["output_byte_identical_to_source"])
                    self.assertEqual(resource["source_sha256"], resource["output_sha256"])
                    self.assertEqual(resource["unrelated_members_verified_unchanged"], resource["garc_member_count"] - 1)
                    self.assertTrue(all(texture["byte_identical_bclim"] for texture in resource["textures"]))
                    self.assertTrue(all(texture["max_channel_delta"] == 0 for texture in resource["textures"]))

    def test_png_roundtrip_supports_rgba_filters_and_validates_crc(self):
        rgba = bytes((20, 40, 60, 255, 80, 100, 120, 0))
        raw = b"\x00" + rgba[:4] + b"\x02" + bytes((60, 60, 60, 1))
        png = (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 2, 8, 6, 0, 0, 0)) +
               _png_chunk(b"IDAT", __import__("zlib").compress(raw)) + _png_chunk(b"IEND", b""))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "filtered.png"
            path.write_bytes(png)
            self.assertEqual(read_png_rgba(path), (1, 2, rgba))
            damaged = bytearray(png)
            damaged[-5] ^= 1
            path.write_bytes(damaged)
            with self.assertRaisesRegex(ValueError, "CRC"):
                read_png_rgba(path)
            profiled = (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)) +
                        _png_chunk(b"sRGB", b"\0") + _png_chunk(b"IDAT", __import__("zlib").compress(b"\0\0\0\0\xff")) +
                        _png_chunk(b"IEND", b""))
            path.write_bytes(profiled)
            with self.assertRaisesRegex(ValueError, "color-profile"):
                read_png_rgba(path)

    def test_png_decoder_unfilters_all_five_standard_row_filters(self):
        import zlib

        width, height = 2, 5
        rows = [bytes((10 + y * 17 + i * 11) & 255 for i in range(width * 4)) for y in range(height)]
        filtered = bytearray()
        bpp = 4
        for y, row in enumerate(rows):
            filter_type = y
            prior = rows[y - 1] if y else bytes(width * 4)
            filtered.append(filter_type)
            for x, value in enumerate(row):
                left = row[x - bpp] if x >= bpp else 0
                up = prior[x]
                up_left = prior[x - bpp] if x >= bpp else 0
                if filter_type == 0:
                    predictor = 0
                elif filter_type == 1:
                    predictor = left
                elif filter_type == 2:
                    predictor = up
                elif filter_type == 3:
                    predictor = (left + up) // 2
                else:
                    p = left + up - up_left
                    pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                    predictor = left if pa <= pb and pa <= pc else (up if pb <= pc else up_left)
                filtered.append((value - predictor) & 255)
        png = (b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
               _png_chunk(b"IDAT", zlib.compress(filtered)) + _png_chunk(b"IEND", b""))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "filters.png"
            path.write_bytes(png)
            self.assertEqual(read_png_rgba(path), (width, height, b"".join(rows)))

    def test_rgba4444_quantization_and_rgba8888_exact_encoding(self):
        with tempfile.TemporaryDirectory() as temp:
            editing = Path(temp) / "editing"
            initialize_editing_workspace(editing)
            manifest = json.loads((editing / "manifest.json").read_text(encoding="utf-8"))
            item4 = next(row for row in manifest["assets"] if row["bclim_format"] == 8)
            item8 = next(row for row in manifest["assets"] if row["bclim_format"] == 9)
            for item in (item4, item8):
                from scripts.build_milestone3i_textures import _effective, _member_pack
                archive = _effective("pokemon-x", item["resource"])[0].read_bytes()
                pack, _, _ = _member_pack(archive, tuple(map(int, item["member"].split("/"))))
                from src.rebuilding.textures import parse_texture_pack
                bclim = next(part["data"] for part in parse_texture_pack(pack) if part["name"] == item["internal_filename"])
                width, height, fmt, original_pixels = decode_bclim(bclim)
                edited = bytearray(original_pixels)
                edited[:4] = bytes((123, 77, 209, 255))
                rebuilt = encode_bclim(bytes(edited), width, height, bclim)
                rw, rh, rf, decoded = decode_bclim(rebuilt)
                self.assertEqual((rw, rh, rf), (width, height, fmt))
                self.assertLessEqual(max(abs(a - b) for a, b in zip(edited, decoded)), 8 if fmt == 8 else 0)
                self.assertEqual(rebuilt[-40:], bclim[-40:])

    def test_candidate_image_change_rebuilds_only_target_members_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            editing = root / "editing"
            initialize_editing_workspace(editing)
            item = next(row for row in json.loads((editing / "manifest.json").read_text(encoding="utf-8"))["assets"]
                        if row["png"] == "fight_text.bclim.png")
            path = editing / item["png"]
            width, height, pixels = read_png_rgba(path)
            changed = bytearray(pixels)
            for index in range(0, len(changed), 4):
                if changed[index + 3]:
                    changed[index:index + 4] = bytes((0, 255, 0, changed[index + 3]))
                    break
            write_png(path, width, height, bytes(changed))
            result = build_images(editing_root=editing, output_root=root / "candidate", dry_run=False)
            for game in result["games"].values():
                resource = next(record for record in game["resources"] if record["resource"] == "a/2/4/0")
                self.assertNotEqual(resource["source_sha256"], resource["output_sha256"])
                game_name = "pokemon-x" if game["title_id"] == "0004000000055D00" else "pokemon-y"
                output = (root / "candidate" / game_name / "romfs/a/2/4/0")
                self.assertTrue(output.exists())
                self.assertTrue(resource["texture_pack_roundtrip_verified"])

    def test_candidate_backup_and_rollback_restore_previous_generated_archives(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            editing = root / "editing"
            output = root / "candidate"
            initialize_editing_workspace(editing)
            first = build_images(editing_root=editing, output_root=output, dry_run=True)
            source_hashes = {resource["resource"]: resource["source_sha256"]
                             for resource in first["games"]["pokemon-x"]["resources"]}
            manifest = json.loads((editing / "manifest.json").read_text(encoding="utf-8"))
            texture = next(row for row in manifest["assets"] if row["png"] == "fight_text.bclim.png")
            png = editing / texture["png"]
            width, height, pixels = read_png_rgba(png)
            altered = bytearray(pixels)
            for offset in range(0, len(altered), 4):
                if altered[offset + 3]:
                    altered[offset] ^= 0x20
                    break
            write_png(png, width, height, bytes(altered))
            build_images(editing_root=editing, output_root=output)
            rolled = restore_candidate(output)
            self.assertEqual(len(rolled), 4)
            for resource, digest in source_hashes.items():
                candidate = output / "pokemon-x/romfs" / Path(*resource.split("/"))
                self.assertEqual(__import__("hashlib").sha256(candidate.read_bytes()).hexdigest(), digest)

    def test_flattened_alpha_and_changed_dimensions_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            editing = Path(temp) / "editing"
            initialize_editing_workspace(editing)
            path = editing / "fight_text.bclim.png"
            width, height, rgba = read_png_rgba(path)
            opaque = bytearray(rgba)
            opaque[3::4] = b"\xff" * (width * height)
            write_png(path, width, height, bytes(opaque))
            with self.assertRaisesRegex(ValueError, "alpha/transparency"):
                build_images(editing_root=editing, output_root=Path(temp) / "candidate")
            write_png(path, width + 1, height, bytes(width + 1 for _ in range((width + 1) * height * 4)))
            with self.assertRaisesRegex(ValueError, "dimensions"):
                build_images(editing_root=editing, output_root=Path(temp) / "candidate")

    def test_editing_workspace_backup_restore_and_corruption_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            editing = root / "editing"
            initialize_editing_workspace(editing)
            original = (editing / "fight_text.bclim.png").read_bytes()
            backup = backup_workspace(editing, root / "backups", EXPECTED_PNGS)
            (editing / "fight_text.bclim.png").write_bytes(b"modified")
            restore_workspace(editing, backup, EXPECTED_PNGS)
            self.assertEqual((editing / "fight_text.bclim.png").read_bytes(), original)
            (backup / "fight_text.bclim.png").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                restore_workspace(editing, backup, EXPECTED_PNGS)

    def test_lz11_literal_encoder_roundtrips_small_and_extended_headers(self):
        for size in (0, 17, 0x1000000):
            payload = bytes((index * 31) & 255 for index in range(size))
            compressed = lz11_literal_compress(payload)
            self.assertEqual(decompress(compressed, max_output=size + 1), payload)

    def test_text_candidate_contains_only_90_scoped_records_and_preserves_pc_mirror(self):
        with tempfile.TemporaryDirectory() as temp:
            result = build_text_candidate(Path(temp) / "text-candidate")
            self.assertEqual(result["translation_records"], 90)
            self.assertEqual(result["included_sources"]["milestone_3h_drafts"], 55)
            self.assertFalse(result["installed"])
            self.assertFalse(result["runtime_tested"])
            self.assertEqual(sum(item["messages_applied"] for item in result["games"]["pokemon-x"]["resources"]), 90)
            for game in ("pokemon-x", "pokemon-y"):
                for resource in result["games"][game]["resources"]:
                    self.assertTrue(resource["translations_applied"])
                    self.assertGreater(resource["untranslated_messages_verified_unchanged"], 0)
            pc_file = Path(temp) / "text-candidate/pokemon-x/romfs/a/0/8/2"
            archive = GARC.parse(pc_file.read_bytes())
            member = next(m for m in archive.members if (m.entry_id, m.subfile_id) == (55, 0))
            text = TextFile.parse(member.data)
            self.assertIn("проверил(а)", text.lines[1].display_text)
            self.assertEqual(text.lines[3].display_text, "…И ты уже без пижамы!")
            removed = rollback_text_candidate(Path(temp) / "text-candidate")
            self.assertEqual(len(removed), 4)


if __name__ == "__main__":
    unittest.main()
