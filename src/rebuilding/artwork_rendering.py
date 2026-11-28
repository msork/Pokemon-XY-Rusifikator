"""Evidence-based lettering masks and style fitting for offline artwork review."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from src.rebuilding.artwork_localization import ReviewRequired, _ROTATIONS, _unrotate_box


def _density(mask: Image.Image) -> float:
    box = mask.getbbox()
    if box is None:
        return 0.0
    return sum(value > 127 for value in mask.crop(box).get_flattened_data()) / ((box[2] - box[0]) * (box[3] - box[1]))


def reference_style(original: Image.Image, edited: Image.Image) -> dict:
    if original.mode != "RGBA" or edited.mode != "RGBA" or original.size != edited.size:
        raise ValueError("Style reference dimensions or mode changed")
    mask = ImageChops.difference(original, edited).convert("RGB")
    channels = mask.split()
    changed = ImageChops.lighter(ImageChops.lighter(*channels[:2]), channels[2])
    changed = ImageChops.lighter(changed, ImageChops.difference(original.getchannel("A"), edited.getchannel("A")))
    changed = changed.point([0] + [255] * 255)
    box = changed.getbbox()
    return {"edit_box": box, "density": round(_density(changed), 4),
            "ink_height": box[3] - box[1] if box else 0}


@lru_cache(maxsize=192)
def _font(path: Path, size: int):
    return ImageFont.truetype(str(path), size)


def _glyphs(text: str, path: Path, size: int, tracking: int) -> Image.Image:
    font = _font(path, size)
    mask = Image.new("L", (max(16, int(font.getlength(text)) + len(text) * abs(tracking) + size * 2),
                           size * 3))
    draw = ImageDraw.Draw(mask)
    if tracking == 0:
        draw.text((size, size // 3), text, font=font, fill=255)
    else:
        x = size
        for glyph in text:
            draw.text((x, size // 3), glyph, font=font, fill=255)
            x += font.getlength(glyph) + tracking
    bounds = mask.getbbox()
    if bounds is None:
        raise ReviewRequired("The selected font produced no visible lettering")
    return mask.crop(bounds)


def _shape_similarity(a: Image.Image, b: Image.Image) -> float:
    a = a.resize((48, 16), Image.Resampling.BOX)
    b = b.resize((48, 16), Image.Resampling.BOX)
    error = sum(abs(x - y) for x, y in zip(a.get_flattened_data(), b.get_flattened_data()))
    return 1 - error / (48 * 16 * 255)


def _slant(mask: Image.Image) -> float:
    """Estimate stroke lean from horizontal ink centroids across central rows."""
    frame = mask.resize((64, 24), Image.Resampling.BOX)
    samples = frame.get_flattened_data()

    def centroid(top, bottom):
        weights = [sum(samples[y * 64 + x] for y in range(top, bottom)) for x in range(64)]
        total = sum(weights)
        return sum(x * value for x, value in enumerate(weights)) / total if total else 31.5

    return (centroid(5, 10) - centroid(14, 19)) / 64


def _choose_lettering(ink: Image.Image, original: str, russian: str, fonts: list[Path],
                      target: tuple[int, int], references: list[dict]) -> tuple[Image.Image, dict]:
    width, height = target
    if height < 7:
        raise ReviewRequired("Native lettering area is below seven pixels")
    comparable = [ref["density"] for ref in references if height * 0.65 <= ref["ink_height"] <= height * 1.45]
    density = median(comparable) if comparable else _density(ink)
    best = None
    source_slant = _slant(ink)
    for font in fonts:
        for tracking in (-1, 0, 1):
            latin = _glyphs(original, font, max(8, round(height * 1.25)), tracking)
            aspect = min(latin.width / latin.height, ink.width / ink.height) / max(
                latin.width / latin.height, ink.width / ink.height)
            slant_fit = max(0, 1 - 6 * abs(_slant(latin) - source_slant))
            match = 0.65 * _shape_similarity(ink, latin) + 0.18 * aspect + 0.17 * slant_fit
            for size in range(max(9, 2 * height), 6, -1):
                mask = _glyphs(russian, font, size, tracking)
                if mask.width <= width and mask.height <= height:
                    legibility = mask.height / height
                    glyph_density = 1 - abs(_density(mask) - density)
                    score = 0.48 * match + 0.32 * legibility + 0.20 * glyph_density
                    if best is None or score > best[0]:
                        best = (score, mask, font.name, tracking, match, legibility, glyph_density, slant_fit)
                    break
    if best is None or best[5] < 0.66 or best[1].height < 7:
        raise ReviewRequired("Cyrillic lettering would lose too much height")
    score, mask, font, tracking, match, height_fit, density_fit, slant_fit = best
    return mask, {"font": font, "tracking": tracking, "shape_match": round(match, 3),
                  "height_fit": round(height_fit, 3), "density_match": round(density_fit, 3),
                  "slant_match": round(slant_fit, 3),
                  "visual_score": round(score, 3)}


def _equal_background(pixel, bg) -> bool:
    return pixel == bg or pixel[3] == bg[3] == 0


def _inspect_lettering(crop: Image.Image, expected: tuple[int, int, int, int]):
    width, height = crop.size
    source = crop.get_flattened_data()
    background = []
    mask = Image.new("L", crop.size)
    mask_pixels = []
    for y in range(height):
        row = source[y * width:(y + 1) * width]
        left = row[0]
        if not all(_equal_background(pixel, left) for pixel in (*row[:2], *row[-2:])):
            raise ReviewRequired("Text crosses artwork or no matching background exists on both sides")
        if left[3] not in (0, 255):
            raise ReviewRequired("Cannot separate lettering from a translucent backing")
        background.append(left)
        mask_pixels.extend(0 if _equal_background(pixel, left) else 255 for pixel in row)
    if len({pixel[3] for pixel in background}) != 1:
        raise ReviewRequired("Detected artwork intersects a transparency boundary")
    mask.putdata(mask_pixels)
    bounds = mask.getbbox()
    if bounds is None or any(abs(x - y) > 3 for x, y in zip(bounds, expected)):
        raise ReviewRequired("Recovered lettering mask disagrees with OCR bounds")
    if bounds[1] == 0 or bounds[3] == height or _density(mask) > 0.88:
        raise ReviewRequired("Lettering mask reaches an artwork boundary or is too dense")
    if background[0][3] == 255 and any(pixel[3] != 255 for pixel in source):
        raise ReviewRequired("Opaque background has unrelated transparency")
    return source, background, mask, bounds


def _common_rgb(colors: list[tuple]) -> tuple[int, int, int]:
    return Counter(color[:3] for color in colors).most_common(1)[0][0]


def _representative_face(samples: list[tuple]) -> tuple[int, int, int]:
    # Select the brighter portion of the inner stroke so a dark border
    # does not become the fill on thin or antialiased letters.
    visible = sorted(samples, key=lambda color: sum(color[:3]))
    return _common_rgb(visible[len(visible) * 2 // 3:])


def _palette_coverage(source, revised, old_mask, new_mask) -> float:
    def histogram(pixels, mask):
        counts = Counter()
        for pixel, active in zip(pixels, mask):
            if active and pixel[3] >= 51:
                counts[tuple(channel // 32 for channel in pixel[:3])] += pixel[3]
        return counts

    before = histogram(source, old_mask)
    after = histogram(revised, new_mask)
    covered = 0
    for color, count in before.items():
        if any(max(abs(a - b) for a, b in zip(color, other)) <= 1 for other in after):
            covered += count
    return covered / sum(before.values()) if before else 0.0


def _effects(source, ink: Image.Image, bounds):
    w, h = ink.size
    inside = ink.filter(ImageFilter.MinFilter(3))
    internal = inside.get_flattened_data()
    ink_pixels = ink.get_flattened_data()
    edge = [p for i, p in enumerate(source) if p[3] and ink_pixels[i] and not internal[i]]
    core = [p for i, p in enumerate(source) if internal[i] and p[3]]
    visible = core or [p for i, p in enumerate(source) if p[3] and ink_pixels[i]]
    fill = _representative_face(visible)
    border = _common_rgb(edge) if edge else fill
    color_gap = sum(abs(a - b) for a, b in zip(fill, border))
    outline = border if core and color_gap >= 64 and sum(p[:3] == border for p in edge) >= 0.22 * len(edge) else None
    row_colors = []
    for y in range(bounds[1], bounds[3]):
        samples = [source[i] for i in range(y * w, (y + 1) * w) if internal[i] and source[i][3]]
        row_colors.append(_representative_face(samples) if samples else None)
    available = [i for i, color in enumerate(row_colors) if color is not None]
    if len(available) >= 3:
        sampled = [row_colors[min(available, key=lambda row: abs(row - y))] for y in range(len(row_colors))]
        gradient = [tuple(round(median(color[channel] for color in sampled[max(0, y - 1):y + 2]))
                          for channel in range(3)) for y in range(len(row_colors))]
    else:
        gradient = [fill] * (bounds[3] - bounds[1])
    shadow = None
    if outline:
        shades = Counter(p[:3] for p in edge if p[:3] not in (fill, outline))
        footprint = {(i % w, i // w) for i, value in enumerate(ink_pixels) if value}
        for shade, count in shades.most_common(3):
            locations = {(i % w, i // w) for i, pixel in enumerate(source)
                         if ink_pixels[i] and pixel[:3] == shade}
            if count < 4 or not locations:
                continue
            front = footprint - locations

            def agreement(offset):
                dx, dy = offset
                displaced = {(x + dx, y + dy) for x, y in front
                             if 0 <= x + dx < w and 0 <= y + dy < h} - front
                return len(displaced & locations) / len(displaced | locations)

            offsets = [(dx, dy) for dx in range(-3, 4) for dy in range(0, 4) if dx or dy]
            offset = max(offsets, key=agreement)
            if agreement(offset) >= 0.65:
                shadow = (offset, shade)
                break
    return inside, gradient, outline, shadow


def _paint_line(image: Image.Image, box: list[int], english: str, russian: str,
                fonts: list[Path], references: list[dict], fmt: int):
    w, h = image.size
    left, top, right, bottom = box
    alpha = image.getchannel("A")
    silhouette = alpha.getbbox()
    # Detached glyph sprites may touch a canvas edge. Transparent corners
    # and a tight single-line footprint permit virtual transparent padding.
    corners = (alpha.getpixel((0, 0)), alpha.getpixel((w - 1, 0)),
               alpha.getpixel((0, h - 1)), alpha.getpixel((w - 1, h - 1)))
    detached = silhouette and not any(corners) and alpha.histogram()[0] >= w * h * 0.15 and all(
        0 <= delta <= max(7, (bottom - top) // 5)
        for delta in (left - silhouette[0], top - silhouette[1], silhouette[2] - right, silhouette[3] - bottom)
    )
    if detached:
        left, top, right, bottom = silhouette
        outer = (left - 5, top - 4, right + 5, bottom + 4)
    else:
        outer = (max(0, left - 5), max(0, top - 4), min(w, right + 5), min(h, bottom + 4))
    crop = image.crop(outer)
    expected = (left - outer[0], top - outer[1], right - outer[0], bottom - outer[1])
    if min(crop.size) < 5:
        raise ReviewRequired("Text crop is too small")
    source, background, ink, bounds = _inspect_lettering(crop, expected)
    inside, gradient, outline, shadow = _effects(source, ink, bounds)
    bw, bh = bounds[2] - bounds[0], bounds[3] - bounds[1]
    guard = int(outline is not None)
    dx, dy = shadow[0] if shadow else (0, 0)
    available = (bw - 2 * guard - abs(dx), bh - 2 * guard - dy)
    mask, profile = _choose_lettering((inside if inside.getbbox() else ink).crop(bounds), english,
                                       russian, fonts, available, references)
    # Keep the source centre for centred labels and the nearer canvas edge for
    # left/right-aligned UI labels.
    source_center = outer[0] + (bounds[0] + bounds[2]) / 2
    if source_center < w * 0.34:
        alignment, margin = "left", 0
    elif source_center > w * 0.66:
        alignment, margin = "right", available[0] - mask.width
    else:
        alignment, margin = "center", (available[0] - mask.width) // 2
    start_x = bounds[0] + guard + max(0, -dx) + margin
    start_y = bounds[1] + guard + (available[1] - mask.height) // 2
    glyph = Image.new("L", crop.size)
    glyph.paste(mask, (start_x, start_y))
    rim = glyph.filter(ImageFilter.MaxFilter(3)) if outline else Image.new("L", crop.size)
    drop = Image.new("L", crop.size)
    if shadow:
        drop.paste(rim, (dx, dy))
    ink_values = ink.get_flattened_data()
    glyph_values = glyph.get_flattened_data()
    rim_values = rim.get_flattened_data()
    drop_values = drop.get_flattened_data()
    alpha_levels = sorted({0, *(p[3] for i, p in enumerate(source) if ink_values[i])})
    visible_alpha = max(alpha_levels)
    sprite = background[0][3] == 0
    crop_result = []
    edits = []
    for i, old in enumerate(source):
        y = i // crop.width
        color = background[y] if ink_values[i] else old
        if sprite and ink_values[i]:
            color = old[:3] + (0,)
        level = glyph_values[i]
        layers = []
        if drop_values[i]:
            layers.append((shadow[1], drop_values[i]))
        if rim_values[i]:
            layers.append((outline, rim_values[i]))
        if level:
            row = min(len(gradient) - 1, max(0, (y - start_y) * len(gradient) // mask.height))
            layers.append((gradient[row], level))
        for rgb, coverage in layers:
            if sprite:
                alpha = min(alpha_levels, key=lambda value: abs(value - visible_alpha * coverage / 255))
                if alpha >= color[3] and alpha:
                    color = (*rgb, alpha)
            else:
                color = tuple(round(a + (b - a) * coverage / 255) for a, b in zip(color[:3], rgb)) + (255,)
        if fmt in (8, 11) and color != old:
            if fmt == 8:
                color = tuple(round(channel / 17) * 17 for channel in color)
            else:
                color = color[:3] + (round(color[3] / 17) * 17,)
        crop_result.append(color)
        edits.append(255 if color != old else 0)
    crop.putdata(crop_result)
    edit = Image.new("L", crop.size)
    edit.putdata(edits)
    painted = [bool(a or b or c) for a, b, c in zip(glyph_values, rim_values, drop_values)]
    profile["palette_coverage"] = round(_palette_coverage(source, crop_result, ink_values, painted), 3)
    profile["width_fit"] = round((mask.width + 2 * guard + abs(dx)) / bw, 3)
    if sprite:
        def soft_share(samples, active):
            alpha = [pixel[3] for pixel, allowed in zip(samples, active) if allowed and pixel[3]]
            return sum(value < 170 for value in alpha) / len(alpha) if alpha else 0

        profile["soft_alpha_drift"] = round(abs(soft_share(source, ink_values) - soft_share(crop_result, painted)), 3)
    else:
        profile["soft_alpha_drift"] = 0.0
    profile.update(background="transparent" if sprite else "row-sampled", gradient=len(set(gradient)) > 1,
                   outline=bool(outline), shadow=bool(shadow), alignment=alignment,
                   region=[outer[0] + v if i % 2 == 0 else outer[1] + v for i, v in enumerate(bounds)])
    return crop, edit, outer[:2], profile


def render_enhanced(image: Image.Image, lines: list[dict], fonts: list[Path], references: list[dict], fmt: int):
    result = image.copy()
    mask = Image.new("L", image.size)
    profiles = []
    regions = Image.new("L", image.size)
    for line in lines:
        rotation = line["rotation"]
        work = image.transpose(_ROTATIONS[rotation]) if rotation else image
        box = _unrotate_box(line["box"], *work.size, (360 - rotation) % 360)
        crop, edit, offset, profile = _paint_line(work, box, line["text"], line["russian"], fonts, references, fmt)
        overlay = work.copy()
        overlay.paste(crop, offset)
        layer = Image.new("L", work.size)
        layer.paste(edit, offset)
        region = Image.new("L", work.size)
        ImageDraw.Draw(region).rectangle((offset[0], offset[1], offset[0] + crop.width - 1,
                                          offset[1] + crop.height - 1), fill=255)
        if rotation:
            inverse = _ROTATIONS[(360 - rotation) % 360]
            overlay, layer, region = (part.transpose(inverse) for part in (overlay, layer, region))
        if ImageChops.multiply(regions, region).getbbox():
            raise ReviewRequired("Recovered line regions overlap")
        regions = ImageChops.lighter(regions, region)
        result.paste(overlay, mask=layer)
        mask = ImageChops.lighter(mask, layer)
        profile["region"] = _unrotate_box(profile["region"], *image.size, rotation)
        profiles.append(profile)
    return result, mask, profiles
