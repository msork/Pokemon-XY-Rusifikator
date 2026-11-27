from __future__ import annotations

import struct
import unittest

from src.extraction.bch import UnsupportedBch, decode_surface, parse_bch, replace_isolated_texture


def words(*values: int) -> bytes:
    return struct.pack(f"<{len(values)}I", *values)


def fixture(*, width=8, height=8, fmt=0, mips=1, cube=False, alias=False, model=False,
            relative=0, extra_ref=False, payload=None) -> bytes:
    """Build a small XY 7/7 archive with independently written PICA commands."""
    counts = 2 if alias else 1
    table = 180
    descriptor = table + counts * 4
    contents = bytearray(descriptor + counts * 32 + (8 if model else 0))
    contents[36:44] = words(table, counts)
    relocations = [9]
    if model:
        model_table = descriptor + counts * 32
        contents[:8] = words(model_table, 1)
        contents[model_table:model_table + 4] = words(model_table + 4)
        relocations.extend((0, model_table // 4))
    commands = bytearray()
    for i in range(counts):
        slot = descriptor + i * 32
        contents[table + i * 4:table + i * 4 + 4] = words(slot)
        offset = len(commands)
        commands += words((width << 16) | height, 0xF0082)
        if mips > 1:
            commands += words((mips - 1) << 16, 0xF0084)
        address_field = len(commands)
        if cube:
            commands += words(relative, 0x805F0085, 256, 512, 768, 1024, 1280, 0)
            relocations.extend(((0x25 << 25) | ((address_field + 4 * n) // 4) for n in range(2, 7)))
        else:
            commands += words(relative, 0xF0085)
        commands += words(fmt, 0xF008E, 1, 0xF023D)
        contents[slot:slot + 8] = words(offset, (len(commands) - offset) // 4)
        contents[slot + 24:slot + 28] = bytes((fmt, mips, 0, 0))
        relocations.extend(((table + i * 4) // 4, (2 << 25) | (slot // 4), (1 << 25) | (slot + 28),
                            (0x24 << 25) | (address_field // 4)))
    if extra_ref:
        relocations.append((0x26 << 25) | len(commands) // 4)
        commands += words(8)
    strings = b"Test texture\x00"
    offset = 56
    buffers = (bytes(contents), strings, bytes(commands),
               payload if payload is not None else bytes(1536 if cube else (1280 if mips > 1 else 256)),
               words(*relocations))
    offsets = []
    tail = bytearray()
    for buffer in buffers:
        while (offset + len(tail)) % 8:
            tail.append(0)
        offsets.append(offset + len(tail))
        tail.extend(buffer)
    return (b"BCH\0" + struct.pack("<BBH", 7, 7, 38669) + words(*offsets, *(len(b) for b in buffers), 0, 0)
            + tail)


class BchTests(unittest.TestCase):
    def test_2d_orientation_exact_mapping_and_unchanged_round_trip(self):
        # The first stored ABGR sample appears on the last PNG row.
        raw = fixture(payload=b"\x61\x22\x33\x44" + bytes(252))
        parsed = parse_bch(raw)
        self.assertFalse(parsed.issues)
        texture, = parsed.textures
        self.assertEqual((texture.name, texture.format, texture.mipmap_count), ("Test texture", 0, 1))
        surface, = texture.surfaces
        self.assertEqual((surface.face, surface.mip_level, surface.width, surface.height), ("2D", 0, 8, 8))
        start = parsed.sections["data"].offset
        self.assertEqual((surface.data_offset, surface.data_length), (start, 256))
        payload = raw[start:start + 256]
        pixels = decode_surface(payload, surface, texture.format)
        self.assertEqual(pixels[:32], bytes(32))
        self.assertEqual(pixels[-32:-28], b"\x44\x33\x22\x61")
        self.assertIs(replace_isolated_texture(raw, 0, payload), raw)
        replacement = b"\xff\x90\x80\x70" + payload[4:]
        changed = replace_isolated_texture(raw, 0, replacement)
        self.assertEqual(changed[:start], raw[:start])
        self.assertEqual(changed[start + 256:], raw[start + 256:])
        self.assertEqual(parse_bch(changed), parsed)
        self.assertEqual(decode_surface(changed[start:start + 256], surface, 0)[-32:-28], b"\x70\x80\x90\xff")

    def test_etc1a4_reuses_pica_color_and_alpha_in_bottom_up_order(self):
        alpha = bytes.fromhex("1032547698badcfe")
        etc = bytes.fromhex("0000000000563412")
        raw = fixture(fmt=13, payload=(alpha + etc) * 4)
        texture, = parse_bch(raw).textures
        surface, = texture.surfaces
        rgba = decode_surface(raw[surface.data_offset:surface.data_offset + surface.data_length], surface, 13)
        self.assertEqual(rgba[-32:-24], bytes((19, 53, 87, 0, 19, 53, 87, 68)))
        self.assertEqual(rgba[-64:-60], bytes((19, 53, 87, 17)))

    def test_cube_faces_use_relocated_consecutive_register_writes(self):
        parsed = parse_bch(fixture(cube=True))
        self.assertFalse(parsed.issues)
        texture, = parsed.textures
        self.assertEqual([surface.face for surface in texture.surfaces], ["+X", "-X", "+Y", "-Y", "+Z", "-Z"])
        self.assertEqual([s.data_offset - parsed.sections["data"].offset for s in texture.surfaces], list(range(0, 1536, 256)))

    def test_mipmaps_keep_dimensions_and_payload_boundaries(self):
        parsed = parse_bch(fixture(width=16, height=16, mips=2))
        self.assertFalse(parsed.issues)
        first, second = parsed.textures[0].surfaces
        self.assertEqual((first.mip_level, first.width, first.data_length), (0, 16, 1024))
        self.assertEqual((second.mip_level, second.width, second.data_offset, second.data_length),
                         (1, 8, first.data_offset + 1024, 256))
        self.assertEqual(len(decode_surface(bytes(256), second, 0)), 256)
        unsupported = parse_bch(fixture(mips=2))
        self.assertEqual(unsupported.issues[0]["status"], "unsupported")
        self.assertIn("smaller than a PICA tile", unsupported.issues[0]["reason"])

    def test_resource_counts_keep_nontextures_out_of_the_output(self):
        report = parse_bch(fixture(model=True))
        self.assertEqual(report.resource_counts["models"], 1)
        self.assertEqual(len(report.textures), 1)
        self.assertFalse(report.issues)

    def test_replacement_rejects_aliases_cubes_other_resource_types_and_unrelated_relocations(self):
        for kwargs in ({"alias": True}, {"cube": True}, {"model": True}, {"extra_ref": True}):
            with self.subTest(**kwargs), self.assertRaises(UnsupportedBch):
                replace_isolated_texture(fixture(**kwargs), 0, bytes(256))
        with self.assertRaisesRegex(ValueError, "original byte length"):
            replace_isolated_texture(fixture(), 0, bytes(255))

    def test_malformed_headers_sections_and_relocations_are_rejected(self):
        raw = fixture()
        with self.assertRaisesRegex(ValueError, "signature"):
            parse_bch(b"BCHx" + raw[4:])
        with self.assertRaises(UnsupportedBch):
            parse_bch(raw[:4] + b"\x08" + raw[5:])
        with self.assertRaisesRegex(ValueError, "trailing data"):
            parse_bch(raw + b"\0")
        overlapping = raw[:12] + raw[8:12] + raw[16:]
        with self.assertRaisesRegex(ValueError, "overlaps"):
            parse_bch(overlapping)
        relocation = parse_bch(raw).sections["relocations"].offset
        with self.assertRaisesRegex(ValueError, "duplicated"):
            parse_bch(raw[:relocation + 4] + raw[relocation:relocation + 4] + raw[relocation + 8:])
        with self.assertRaisesRegex(ValueError, "source is out of bounds"):
            parse_bch(raw[:relocation] + words(0x1FFFFFF) + raw[relocation + 4:])

    def test_bad_texture_span_and_command_packet_are_reported(self):
        parsed = parse_bch(fixture(relative=8))
        self.assertEqual(parsed.issues[0]["status"], "failed")
        self.assertIn("exceeds the data section", parsed.issues[0]["reason"])
        raw = fixture()
        header = parse_bch(raw).sections["commands"].offset + 4
        bad = raw[:header] + words(0x7FFF0082) + raw[header + 4:]
        self.assertIn("Truncated BCH PICA command packet", parse_bch(bad).issues[0]["reason"])
        overlap = parse_bch(fixture(extra_ref=True))
        self.assertIn("spans another relocated data target", overlap.issues[0]["reason"])
        unknown = parse_bch(fixture(fmt=14))
        self.assertEqual(unknown.issues[0]["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
