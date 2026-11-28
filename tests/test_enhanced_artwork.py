from pathlib import Path
from types import SimpleNamespace
import struct
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.rebuilding.artwork_localization import (
    ReviewRequired, Translator, _ROTATIONS, _unrotate_box, classify_english, local_paddle, multi_pass_ocr, text_key,
)
from scripts.localize_textures import russian_key
from src.rebuilding.artwork_rendering import _effects, reference_style, render_enhanced
from src.rebuilding.bclim import decode_bclim, recompress_bclim_etc


def fixture(fmt: int, payload: bytes) -> bytes:
    return payload + struct.pack("<4sHHIII4sIHHII", b"CLIM", 0xFEFF, 20, 0x02020000,
                                 len(payload) + 40, 1, b"imag", 16, 8, 8, fmt, len(payload))


class EnhancedArtworkTests(unittest.TestCase):
    def test_rotation_boxes_map_back_into_non_square_native_image(self):
        image = Image.new("L", (76, 32))
        ImageDraw.Draw(image).rectangle((11, 8, 29, 19), fill=255)
        for angle, transform in _ROTATIONS.items():
            bounds = image.transpose(transform).getbbox()
            self.assertEqual(_unrotate_box(bounds, *image.size, angle), [11, 8, 30, 20])

    def test_multi_pass_retains_native_boxes_and_groups_lines(self):
        image = Image.new("RGBA", (80, 50), (255, 255, 255, 255))
        fixture_lines = [{"text": "HIGH", "confidence": 90, "box": [42, 42, 132, 96]},
                         {"text": "SCORE", "confidence": 91, "box": [42, 120, 152, 174]}]
        # The rotated passes are blank in this fixture.
        def read(frame, *args):
            return fixture_lines if frame.width > frame.height and args[-1] != 11 else []
        with patch("src.rebuilding.artwork_localization._read_lines", side_effect=read):
            lines = multi_pass_ocr(image, Path("tesseract"), Path("tessdata"))
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["box"], [5, 5, 20, 14])
        self.assertEqual(classify_english(lines, "score.bclim", set())[0], "multiline_english")

    def test_language_gate_rejects_locales_ambiguity_and_unconfirmed_word(self):
        def line(value):
            return {"text": value, "box": [4, 4, 90, 22], "confidence": 96, "rotation": 0,
                    "passes": ["light", "dark"], "competing_confidence": 0}
        self.assertEqual(classify_english([line("FIN")], "the_end_txt.bclim", set()),
                         ("other_language_or_locale", []))
        self.assertEqual(classify_english([line("DRÜCKE START")], "push_start.bclim", set()), ("other_language_or_locale", []))
        self.assertEqual(classify_english([line("POKÉDEX")], "zkn_title00.bclim", set())[0], "english")
        self.assertEqual(text_key("Ёж!"), text_key("Еж"))

    def test_context_resolves_only_matching_glossary_and_russian_keeps_yo(self):
        translator = Translator.__new__(Translator)
        translator.terms = {"pokedex": {"Покедекс", "ПОКЕДЕКС"}}
        translator.contextual_terms = {"pokedex": {"ui": {"Покедекс"}, "battle_ui": {"ПОКЕДЕКС"}}}
        with self.assertRaisesRegex(ReviewRequired, "terminology"):
            translator("POKEDEX")
        self.assertEqual(translator("POKEDEX", ("ui",)), ("ПОКЕДЕКС", "glossary"))
        self.assertNotEqual(russian_key("Ёж"), russian_key("Еж"))

    def test_optional_paddle_uses_supplied_local_model(self):
        def recognition(**options):
            self.assertEqual(options["model_dir"], "local-model")
            self.assertEqual(options["device"], "gpu")
            return SimpleNamespace(predict=lambda frame, batch_size: [
                SimpleNamespace(json={"res": {"rec_text": "SCORE", "rec_score": 0.95}})
            ])

        modules = {"paddleocr": SimpleNamespace(TextRecognition=recognition),
                   "numpy": SimpleNamespace(asarray=lambda frame: frame)}
        with patch.dict("sys.modules", modules), patch.dict("os.environ"):
            adapter = local_paddle(Path("local-model"), "test-rec", "gpu")
            self.assertEqual(adapter(Image.new("RGBA", (32, 12))), ("SCORE", 95.0))

    def test_mask_and_row_background_preserve_unrelated_pixels(self):
        image = Image.new("RGBA", (160, 40))
        draw = ImageDraw.Draw(image)
        for y in range(image.height):
            draw.line((0, y, 159, y), fill=(y, y, y, 255))
        font = ImageFont.load_default(size=23)
        ink = Image.new("L", image.size)
        d = ImageDraw.Draw(ink)
        d.text((14, 3), "HIGH SCORE", font=ImageFont.load_default(size=16), fill=255)
        bbox = ink.getbbox()
        image.paste((230, 230, 230, 255), mask=ink)
        draw.point((1, 1), fill="red")
        line = {"text": "HIGH SCORE", "russian": "РЕКОРД", "box": bbox, "rotation": 0}
        with patch("src.rebuilding.artwork_rendering._font", return_value=font):
            # Use an independent raster fixture for a stable Cyrillic-capable
            # glyph candidate when the Pillow embedded font lacks Cyrillic.
            candidate = ink.crop(bbox)
            candidate = candidate.resize((candidate.width - 7, candidate.height))
            with patch("src.rebuilding.artwork_rendering._glyphs", return_value=candidate):
                output, mask, metrics = render_enhanced(image, [line], [Path("fixture.ttf")], [], 9)
        self.assertEqual(output.size, image.size)
        self.assertEqual(output.getchannel("A").tobytes(), image.getchannel("A").tobytes())
        self.assertEqual(output.getpixel((1, 1)), image.getpixel((1, 1)))
        self.assertEqual(metrics[0]["background"], "row-sampled")
        self.assertTrue(all(a == b or permission for a, b, permission in
                            zip(image.get_flattened_data(), output.get_flattened_data(), mask.get_flattened_data())))
        self.assertGreater(reference_style(image, output)["ink_height"], 0)

    def test_stylized_ink_recovers_gradient_outline_and_shadow_direction(self):
        glyph = Image.new("L", (75, 45))
        draw = ImageDraw.Draw(glyph)
        for box in ((10, 9, 12, 30), (20, 9, 22, 30), (10, 18, 22, 21), (31, 9, 34, 30)):
            draw.rectangle(box, fill=255)
        outline = glyph.filter(ImageFilter.MaxFilter(3))
        shadow = Image.new("L", glyph.size)
        shadow.paste(outline, (2, 3))
        image = Image.new("RGBA", glyph.size)
        image.paste((40, 0, 20, 255), mask=shadow)
        image.paste((15, 15, 15, 255), mask=outline)
        gradient = Image.new("RGBA", glyph.size)
        draw = ImageDraw.Draw(gradient)
        for y in range(glyph.height):
            draw.line((0, y, glyph.width - 1, y), fill=(240 - y * 3, 235 - y * 2, 210 - y * 2, 255))
        image.paste(gradient, mask=glyph)
        ink = image.getchannel("A")
        _, colors, recovered_outline, recovered_shadow = _effects(image.get_flattened_data(), ink, ink.getbbox())
        self.assertGreater(len(set(colors)), 10)
        self.assertEqual(recovered_outline, (15, 15, 15))
        self.assertEqual(recovered_shadow, ((2, 3), (40, 0, 20)))

    def test_changed_etc1_endpoints_and_protected_texels(self):
        original = fixture(10, bytes(32))
        pixels = bytearray(decode_bclim(original)[3])
        mask = bytearray(64)
        for y in range(4):
            for x in range(2):
                i = y * 8 + x
                pixels[i * 4:i * 4 + 3] = bytes((197, 27, 61))
                mask[i] = 255
        rebuilt, quality = recompress_bclim_etc(bytes(pixels), original, bytes(mask))
        self.assertNotEqual(rebuilt[:8], original[:8])
        self.assertEqual(rebuilt[8:], original[8:])
        self.assertLessEqual(quality["max_rgb_error"], 12)
        self.assertLessEqual(quality["rms_rgb_error"], 5)
        unchanged = decode_bclim(original)[3]
        new = decode_bclim(rebuilt)[3]
        self.assertTrue(all(new[i * 4:i * 4 + 4] == unchanged[i * 4:i * 4 + 4]
                            for i in range(64) if not mask[i]))
        with self.assertRaisesRegex(ValueError, "protected texels"):
            recompress_bclim_etc(bytes(pixels), original, bytes(64))

    def test_etc1a4_recompresses_rgb_and_changes_alpha_only_in_the_requested_half(self):
        original = fixture(11, bytes(64))
        rgba = bytearray(decode_bclim(original)[3])
        allowed = bytearray(64)
        for y in range(4):
            for x in range(2):
                i = y * 8 + x
                rgba[4 * i:4 * i + 4] = bytes((197, 27, 61, 119))
                allowed[i] = 255
        rebuilt, stats = recompress_bclim_etc(bytes(rgba), original, bytes(allowed))
        self.assertNotEqual(rebuilt[8:16], original[8:16])
        self.assertEqual(rebuilt[16:], original[16:])
        self.assertEqual(decode_bclim(rebuilt)[3][3::4], rgba[3::4])
        self.assertLessEqual(stats["rms_rgb_error"], 5)

    def test_etc1a4_alpha_is_exact_and_unchanged_payload_is_identical(self):
        original = fixture(11, bytes(64))
        rgba = decode_bclim(original)[3]
        same, _ = recompress_bclim_etc(rgba, original, bytes(64))
        self.assertIs(same, original)
        mask = bytes((255,)) + bytes(63)
        changed = rgba[:3] + b"\x77" + rgba[4:]
        rebuilt, _ = recompress_bclim_etc(changed, original, mask)
        self.assertEqual(rebuilt[0], 7)
        self.assertEqual(rebuilt[1:], original[1:])
        self.assertEqual(decode_bclim(rebuilt)[3], changed)
        with self.assertRaisesRegex(ValueError, "exact four-bit alpha"):
            recompress_bclim_etc(rgba[:3] + b"\x78" + rgba[4:], original, mask)


if __name__ == "__main__":
    unittest.main()
