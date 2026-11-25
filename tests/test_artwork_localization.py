from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from scripts.scan_milestone3n_artwork import _record_bch, unsupported_formats
from src.rebuilding.artwork_localization import ReviewRequired, glossary_key, render
from src.rebuilding.installation import azaharplus_paths


class ArtworkLocalizationTests(unittest.TestCase):
    def test_flat_lettering_preserves_pixels_outside_text_and_existing_palette(self):
        image = Image.new("RGBA", (64, 28), "#333333")
        draw = ImageDraw.Draw(image)
        draw.rectangle((11, 8, 33, 20), fill="white")
        draw.point((50, 14), fill="red")
        # The bundled font keeps the test independent of host-installed fonts.
        font = ImageFont.load_default(size=12)
        with patch("src.rebuilding.artwork_localization.ImageFont.truetype", return_value=font):
            rendered = render(image, [11, 8, 34, 21], "ОЗ", Path("fixture.ttf"))
        self.assertEqual(rendered.size, image.size)
        self.assertEqual(rendered.getchannel("A").tobytes(), image.getchannel("A").tobytes())
        self.assertEqual(rendered.crop((34, 0, 64, 28)).tobytes(), image.crop((34, 0, 64, 28)).tobytes())
        self.assertTrue(set(rendered.get_flattened_data()) <= set(image.get_flattened_data()))
        self.assertNotEqual(rendered.tobytes(), image.tobytes())

    def test_artwork_touching_ocr_region_boundary_is_held(self):
        image = Image.new("RGBA", (64, 28), "#333333")
        ImageDraw.Draw(image).line((8, 5, 40, 5), fill="red")
        with self.assertRaisesRegex(ReviewRequired, "nonuniform"):
            render(image, [11, 8, 34, 21], "ОЗ", Path("fixture.ttf"))

    def test_glossary_key_matches_accentless_ocr(self):
        self.assertEqual(glossary_key("POKEDEX"), glossary_key("Pokédex"))

    def test_existing_linux_xdg_profile_and_override(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / "azaharplus-emu"
            mods = profile / "load/mods"
            mods.mkdir(parents=True)
            with patch("sys.platform", "linux"), patch("os.environ", {"XDG_DATA_HOME": temp}):
                self.assertEqual(azaharplus_paths(), (profile.resolve(), mods.resolve()))
            with patch("os.environ", {"AZAHARPLUS_DATA_DIR": str(profile)}):
                self.assertEqual(azaharplus_paths(), (profile.resolve(), mods.resolve()))

    def test_bch_inventory_distinguishes_headers_from_internal_byte_sequences(self):
        failures = []
        stats = Counter()
        _record_bch(b"BCH\0header", "a/0/0/0", "0/0", stats, failures)
        _record_bch(b"embedded BCH\0bytes", "a/0/0/0", "1/0", stats, failures)
        inventory = unsupported_formats(failures)
        self.assertEqual(inventory["BCH header"]["occurrences"], 1)
        self.assertEqual(inventory["BCH header"]["locations"][0]["nested_member"], "0/0")


if __name__ == "__main__":
    unittest.main()
