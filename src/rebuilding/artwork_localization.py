"""Offline OCR, glossary lookup and conservative texture lettering."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata

from PIL import Image, ImageDraw, ImageFont


class ReviewRequired(ValueError):
    """The texture cannot be edited safely with the current heuristics."""


def ocr(image: Image.Image, executable: Path, tessdata: Path) -> list[dict]:
    """Read sparse text on light and dark composites and keep the stronger pass."""
    scale = max(1, min(4, 1600 // max(image.size)))
    border = 12
    passes = []
    for backdrop in (255, 0):
        canvas = Image.new("L", (image.width * scale + 2 * border, image.height * scale + 2 * border), 255)
        composite = Image.new("RGBA", image.size, (backdrop,) * 3 + (255,))
        composite.alpha_composite(image)
        gray = composite.convert("L").resize((image.width * scale, image.height * scale), Image.Resampling.BICUBIC)
        if backdrop == 0:
            gray = gray.point(lambda value: 255 - value)
        canvas.paste(gray, (border, border))
        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        result = subprocess.run(
            [str(executable), "stdin", "stdout", "--tessdata-dir", str(tessdata),
             "-l", "eng", "--psm", "11", "-c", "tessedit_create_tsv=1"],
            input=buffer.getvalue(), capture_output=True, check=True, timeout=60,
            env={**os.environ, "OMP_THREAD_LIMIT": "1"},
        )
        groups = defaultdict(list)
        for word in csv.DictReader(StringIO(result.stdout.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE):
            if word["level"] == "5" and word["text"].strip():
                groups[tuple(word[key] for key in ("block_num", "par_num", "line_num"))].append(word)
        lines = []
        for words in groups.values():
            x = min(int(word["left"]) for word in words) - border
            y = min(int(word["top"]) for word in words) - border
            right = max(int(w["left"]) + int(w["width"]) for w in words) - border
            bottom = max(int(w["top"]) + int(w["height"]) for w in words) - border
            lines.append({
                "english": " ".join(word["text"] for word in words),
                "confidence": min(float(word["conf"]) for word in words),
                "box": [max(0, x // scale), max(0, y // scale),
                        min(image.width, -(-right // scale)), min(image.height, -(-bottom // scale))],
            })
        passes.append(lines)
    return max(passes, key=lambda lines: sum(
        max(0, line["confidence"] - 55) * len(line["english"]) for line in lines
    ))


def glossary_key(text: str) -> str:
    return "".join(character for character in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(character))


class Translator:
    def __init__(self, glossary: bytes, model_dir: Path):
        import ctranslate2
        import sentencepiece

        categories = json.loads(glossary)["categories"]
        self.terms = defaultdict(set)
        for records in categories.values():
            for record in records:
                self.terms[glossary_key(record["source"])].add(record["russian"])
        metadata = json.loads((model_dir / "metadata.json").read_bytes())
        if (metadata["from_code"], metadata["to_code"]) != ("en", "ru"):
            raise ValueError("Expected a direct English-to-Russian Argos model")
        self.tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(model_dir / "sentencepiece.model"))
        self.model = ctranslate2.Translator(str(model_dir / "model"), device="cpu", intra_threads=1)

    def __call__(self, english: str) -> tuple[str, str]:
        terms = self.terms.get(glossary_key(english))
        if terms:
            if len(terms) != 1 or None in terms:
                raise ReviewRequired("The glossary requires terminology review")
            russian, = terms
            method = "glossary"
        else:
            result, = self.model.translate_batch([self.tokenizer.encode(english.lower() if english.isupper() else english, out_type=str)], beam_size=4)
            russian = self.tokenizer.decode(result.hypotheses[0])
            method = "offline_model"
        russian = russian.upper() if english.isupper() else russian
        if not re.search("[А-Яа-яЁё]", russian) or any(
            character.isalpha() and not re.fullmatch("[А-Яа-яЁё]", character) for character in russian
        ) or not russian.isprintable():
            raise ReviewRequired("Translation contains unsupported text")
        return russian, method


def render(image: Image.Image, box: list[int], russian: str, font_path: Path) -> Image.Image:
    """Replace lettering only where a flat background and its palette can be inferred."""
    x0, y0, x1, y1 = box
    outer = (max(0, x0 - 3), max(0, y0 - 3), min(image.width, x1 + 3), min(image.height, y1 + 3))
    crop = image.crop(outer)
    width, height = crop.size
    if width < 5 or height < 5:
        raise ReviewRequired("Text region is too small")
    # Ignore hidden RGB when classifying transparent pixels. Preserve it in the output.
    pixels = [p if p[3] else (0, 0, 0, 0) for p in crop.get_flattened_data()]
    edge = {p for i, p in enumerate(pixels) if i % width in (0, width - 1) or i // width in (0, height - 1)}
    if len(edge) != 1:
        raise ReviewRequired("Text touches artwork or a nonuniform background")
    background, = edge
    colors = Counter(pixels)
    del colors[background]
    foreground_rgb = {color[:3] for color in colors}
    alpha_levels = sorted({0, *(color[3] for color in colors)})
    monochrome_sprite = background[3] == 0 and len(foreground_rgb) == 1 and alpha_levels[-1] == 255
    opaque_ramp = (background[3] == 255 and len(colors) > 2 and
                   max(background[:3]) - min(background[:3]) == 0 and
                   all(color[3] == 255 and max(color[:3]) - min(color[:3]) <= 17 for color in colors) and
                   (all(min(color[:3]) >= background[0] for color in colors) or
                    all(max(color[:3]) <= background[0] for color in colors)))
    if not (monochrome_sprite or opaque_ramp) and (
        len(colors) not in (1, 2) or any(color[3] != 255 for color in colors) or background[3] not in (0, 255)
    ):
        raise ReviewRequired("Text has a complex palette or partial alpha")
    fill, *rest = colors
    outline = None
    if rest and not (monochrome_sprite or opaque_ramp):
        # An outline must surround the interior color on all four sides.
        for candidate, stroke in (tuple(colors), tuple(reversed(colors))):
            if all(all(pixels[i + offset] in (candidate, stroke) for offset in (-1, 1, -width, width))
                   for i, p in enumerate(pixels) if p == candidate):
                fill, outline = candidate, stroke
                break
        if outline is None:
            raise ReviewRequired("Cannot distinguish outline from adjacent artwork")
    ink = Image.new("L", crop.size)
    ink.putdata([255 if p != background else 0 for p in pixels])
    left, top, right, bottom = ink.getbbox()
    margins = (x0 - outer[0], y0 - outer[1], x1 - outer[0], y1 - outer[1])
    if any(abs(a - b) > 2 for a, b in zip((left, top, right, bottom), margins)):
        raise ReviewRequired("Foreground extent differs from the OCR bounds")
    # Empty space surrounding the detected lettering is preserved.
    stroke_width = int(outline is not None)
    for size in range(2 * (bottom - top), 5, -1):
        font = ImageFont.truetype(str(font_path), size)
        bounds = font.getbbox(russian, stroke_width=stroke_width)
        text_width, text_height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        if text_width <= right - left and text_height <= bottom - top:
            break
    else:
        raise ReviewRequired("Cyrillic lettering does not fit at a legible size")
    position = (left + (right - left - text_width) // 2 - bounds[0],
                top + (bottom - top - text_height) // 2 - bounds[1])
    if background[3] == 0:
        alpha = crop.getchannel("A")
        alpha.paste(0, (0, 0, width, height), ink)
        crop.putalpha(alpha)
    else:
        crop.paste(background, (0, 0, width, height), ink)
    if monochrome_sprite or opaque_ramp:
        mask = Image.new("L", crop.size)
        ImageDraw.Draw(mask).text(position, russian, font=font, fill=255)
        if monochrome_sprite:
            mask = mask.point([min(alpha_levels, key=lambda alpha: abs(alpha - value)) for value in range(256)])
            color, = foreground_rgb
            letters = Image.new("RGBA", crop.size, color + (255,))
            letters.putalpha(mask)
        else:
            palette = [background, *colors]
            fill = max(colors, key=lambda color: abs(sum(color[:3]) - sum(background[:3])))
            lookup = [
                min(palette, key=lambda color: sum(
                    (sample - (bg + (fg - bg) * level / 255)) ** 2
                    for sample, bg, fg in zip(color[:3], background[:3], fill[:3])
                ))
                for level in range(256)
            ]
            letters = Image.new("RGBA", crop.size)
            letters.putdata([lookup[level] for level in mask.get_flattened_data()])
        crop.paste(letters, mask=mask.point([0] + [255] * 255))
    else:
        for color, stroke in ([(outline, 1)] if outline else []) + [(fill, 0)]:
            mask = Image.new("1", crop.size)
            ImageDraw.Draw(mask).text(position, russian, font=font, fill=1, stroke_width=stroke)
            crop.paste(color, (0, 0, width, height), mask)
    output = image.copy()
    output.paste(crop, outer[:2])
    return output
