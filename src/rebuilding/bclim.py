"""Little-endian XY BCLIM layout, RGBA export and template-based editing."""

from __future__ import annotations

from dataclasses import dataclass
import struct


class UnsupportedBclim(ValueError):
    """A BCLIM feature or storage layout lacks a verified implementation."""


BITS_PER_TEXEL = (8, 8, 8, 16, 16, 16, 24, 16, 16, 32, 4, 8, 4, 4)
ETC_FORMATS = (10, 11)
ETC_MODIFIERS = (
    (2, 8, -2, -8), (5, 17, -5, -17), (9, 29, -9, -29), (13, 42, -13, -42),
    (18, 60, -18, -60), (24, 80, -24, -80), (33, 106, -33, -106), (47, 183, -47, -183),
)


def morton_xy(index: int) -> tuple[int, int]:
    x = (index & 1) | ((index >> 1) & 2) | ((index >> 2) & 4)
    y = ((index >> 1) & 1) | ((index >> 2) & 2) | ((index >> 3) & 4)
    return x, y


MORTON_COORDINATES = tuple(morton_xy(index) for index in range(64))
MORTON_INDEX = {xy: index for index, xy in enumerate(MORTON_COORDINATES)}


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    format: int
    data_size: int
    storage_width: int
    storage_height: int
    palette_size: int = 0

    def tiles(self):
        """Yield offsets and coordinates for tiles that intersect the image."""
        stride = self.storage_width // 8
        for y in range(0, self.height, 8):
            for x in range(0, self.width, 8):
                yield (y // 8) * stride + x // 8, x, y


def bclim_layout(raw: bytes) -> Layout:
    footer = len(raw) - 40
    if footer < 0 or raw[footer:footer + 4] != b"CLIM":
        raise ValueError("BCLIM footer not at expected final 40-byte position")
    if raw[footer + 4:footer + 6] != b"\xff\xfe":
        raise UnsupportedBclim("Unsupported BCLIM byte order")
    if (raw[footer + 6:footer + 8] != b"\x14\x00"
            or struct.unpack_from("<II4sI", raw, footer + 12) != (len(raw), 1, b"imag", 16)):
        raise ValueError("Invalid BCLIM header or imag section")
    width, height, fmt, data_size = struct.unpack_from("<HHII", raw, footer + 28)
    if not width or not height or data_size != footer:
        raise ValueError("Invalid BCLIM dimensions or pixel-data length")
    if fmt >= len(BITS_PER_TEXEL):
        raise UnsupportedBclim(f"BCLIM format {fmt} is unsupported")

    power_width = max(8, 1 << (width - 1).bit_length())
    power_height = max(8, 1 << (height - 1).bit_length())
    if fmt == 7 and raw[:2] == b"\x02\x00":
        count = int.from_bytes(raw[2:4], "little")
        if 1 <= count <= 256:
            side = max(power_width, power_height)
            last_x, last_y = width - 1, height - 1
            last_tile = (last_y // 8) * (side // 8) + last_x // 8
            last_index = 64 * last_tile + MORTON_INDEX[last_x % 8, last_y % 8]
            index_divisor = 2 if count <= 16 else 1
            index_start = 4 + 2 * count
            full_plane_end = index_start + side * side // index_divisor
            if (index_start + last_index // index_divisor < data_size
                    and not any(raw[full_plane_end:data_size])):
                return Layout(width, height, fmt, data_size, side, side, count)
        # A direct RGB5A1 texture can also begin with the word 0x0002. The
        # XY indexed variant uses zero-filled padding after its index plane.

    candidates = [(power_width, power_height)]
    if fmt in ETC_FORMATS:
        candidates.insert(0, (max(16, power_width), max(16, power_height)))
    if fmt == 9:
        candidates.append(((width + 7) & ~7, (height + 7) & ~7))
    for storage_width, storage_height in candidates:
        if storage_width * storage_height * BITS_PER_TEXEL[fmt] == data_size * 8:
            return Layout(width, height, fmt, data_size, storage_width, storage_height)
    raise UnsupportedBclim(f"Unsupported padded BCLIM storage for {width}x{height}, format {fmt}, bytes {data_size}")


def _expand5(value: int) -> int:
    return (value << 3) | (value >> 2)


def _direct_color(data: bytes, offset: int, fmt: int) -> bytes:
    value = data[offset]
    if fmt == 9:
        return data[offset:offset + 4][::-1]
    if fmt == 6:
        return data[offset:offset + 3][::-1] + b"\xff"
    if fmt in (5, 7, 8):
        value |= data[offset + 1] << 8
        if fmt == 8:
            return bytes(((value >> shift) & 15) * 17 for shift in (12, 8, 4, 0))
        if fmt == 7:
            return bytes((_expand5(value >> 11), _expand5((value >> 6) & 31),
                          _expand5((value >> 1) & 31), 255 * (value & 1)))
        green = (value >> 5) & 63
        return bytes((_expand5(value >> 11), (green << 2) | (green >> 4), _expand5(value & 31), 255))
    if fmt == 3:
        luminance = data[offset + 1]
        return bytes((luminance, luminance, luminance, value))
    if fmt == 4:
        return bytes((data[offset + 1], value, 0, 255))
    if fmt == 2:
        return bytes((17 * (value >> 4),)) * 3 + bytes((17 * (value & 15),))
    if fmt in (1, 13):
        return bytes((0, 0, 0, value))
    return bytes((value, value, value, 255))


def _packed_nibble(data: bytes, index: int, *, high_first: bool = False) -> int:
    shift = 4 * ((index & 1) ^ high_first)
    return (data[index // 2] >> shift) & 15


def _write_nibble(data: bytearray, index: int, value: int, *, high_first: bool = False) -> None:
    shift = 4 * ((index & 1) ^ high_first)
    offset = index // 2
    data[offset] = (data[offset] & ~(15 << shift)) | (value << shift)


def _palette_colors(raw: bytes, layout: Layout) -> tuple[bytes, ...]:
    return tuple(_direct_color(raw, 4 + 2 * index, 7) for index in range(layout.palette_size))


def _etc_colors(word: int) -> tuple[tuple[bytes, ...], tuple[bytes, ...]]:
    channels = tuple((word >> shift) & 255 for shift in (56, 48, 40))
    if word & (1 << 33):
        base = tuple(channel >> 3 for channel in channels)
        delta = tuple((channel & 3) - (channel & 4) for channel in channels)
        other = tuple(value + change for value, change in zip(base, delta))
        if any(not 0 <= value <= 31 for value in other):
            raise ValueError("ETC1 differential color exceeds its five-bit range")
        colors = (tuple(map(_expand5, base)), tuple(map(_expand5, other)))
    else:
        colors = (tuple((channel >> 4) * 17 for channel in channels),
                  tuple((channel & 15) * 17 for channel in channels))
    first, second = (
        tuple(bytes(min(255, max(0, channel + modifier)) for channel in base)
              for modifier in ETC_MODIFIERS[(word >> shift) & 7])
        for base, shift in zip(colors, (37, 34))
    )
    return first, second


def _etc_pixels(layout: Layout):
    block_size = 16 if layout.format == 11 else 8
    for tile, tile_x, tile_y in layout.tiles():
        for block in range(4):
            x = tile_x + (block & 1) * 4
            y = tile_y + (block >> 1) * 4
            if x < layout.width and y < layout.height:
                yield (tile * 4 + block) * block_size, x, y


def _decode_etc(raw: bytes, layout: Layout, rgba: bytearray) -> None:
    has_alpha = layout.format == 11
    for offset, x, y in _etc_pixels(layout):
        rgb_offset = offset + 8 if has_alpha else offset
        word = int.from_bytes(raw[rgb_offset:rgb_offset + 8], "little")
        colors = _etc_colors(word)
        flip = bool(word & (1 << 32))
        alpha = int.from_bytes(raw[offset:offset + 8], "little") if has_alpha else (1 << 64) - 1
        for dy in range(min(4, layout.height - y)):
            for dx in range(min(4, layout.width - x)):
                index = dx * 4 + dy
                selector = ((word >> index) & 1) | ((word >> (index + 15)) & 2)
                rgb = colors[(dy if flip else dx) // 2][selector]
                dst = ((y + dy) * layout.width + x + dx) * 4
                rgba[dst:dst + 4] = rgb + bytes((((alpha >> (4 * index)) & 15) * 17,))


def _texels(layout: Layout):
    for tile, x, y in layout.tiles():
        for index, (dx, dy) in enumerate(MORTON_COORDINATES):
            if x + dx < layout.width and y + dy < layout.height:
                yield 64 * tile + index, ((y + dy) * layout.width + x + dx) * 4


def _decode(raw: bytes, layout: Layout) -> bytes:
    rgba = bytearray(layout.width * layout.height * 4)
    fmt = layout.format
    if fmt in ETC_FORMATS:
        _decode_etc(raw, layout, rgba)
    elif layout.palette_size:
        palette = _palette_colors(raw, layout)
        indices = raw[4 + len(palette) * 2:layout.data_size]
        for index, dst in _texels(layout):
            color = _packed_nibble(indices, index, high_first=True) if len(palette) <= 16 else indices[index]
            if color >= len(palette):
                raise ValueError("XY RGB5A1 palette index is out of range")
            rgba[dst:dst + 4] = palette[color]
    elif fmt in (12, 13):
        for index, dst in _texels(layout):
            channel = _packed_nibble(raw, index) * 17
            rgba[dst:dst + 4] = bytes((channel,) * 3 + (255,)) if fmt == 12 else bytes((0, 0, 0, channel))
    else:
        pixel_size = BITS_PER_TEXEL[fmt] // 8
        for index, dst in _texels(layout):
            rgba[dst:dst + 4] = _direct_color(raw, index * pixel_size, fmt)
    return bytes(rgba)


def decode_tiled_rgba(raw: bytes, width: int, height: int, fmt: int) -> bytes:
    """Decode a raw, whole-tile PICA plane using the shared BCLIM format mapping."""
    if min(width, height) < 8 or width % 8 or height % 8:
        raise ValueError("PICA plane dimensions must contain whole 8x8 tiles")
    if not 0 <= fmt < len(BITS_PER_TEXEL):
        raise UnsupportedBclim(f"Unsupported PICA plane format {fmt}")
    if width * height * BITS_PER_TEXEL[fmt] != len(raw) * 8:
        raise ValueError("PICA plane length does not match its dimensions and format")
    return _decode(raw, Layout(width, height, fmt, len(raw), width, height))


def decode_bclim(raw: bytes) -> tuple[int, int, int, bytes]:
    layout = bclim_layout(raw)
    return layout.width, layout.height, layout.format, _decode(raw, layout)


def _encode_direct(rgba: bytes, fmt: int) -> bytes:
    r, g, b, a = rgba
    if fmt == 9:
        return rgba[::-1]
    if fmt == 6:
        return bytes((b, g, r))
    if fmt == 5:
        word = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    elif fmt == 7:
        word = ((r >> 3) << 11) | ((g >> 3) << 6) | ((b >> 3) << 1) | (a >> 7)
    elif fmt == 8:
        word = sum(round(channel / 17) << shift for channel, shift in zip(rgba, (12, 8, 4, 0)))
    elif fmt == 4:
        return bytes((g, r))
    elif fmt == 3:
        return bytes((a, r))
    elif fmt == 2:
        return bytes(((r // 17 << 4) | (a // 17),))
    elif fmt == 1:
        return bytes((a,))
    else:
        return bytes((r,))
    return word.to_bytes(2, "little")


def _encode_etc(pixels: bytearray, rgba: bytes, old: bytes, layout: Layout) -> None:
    has_alpha = layout.format == 11
    for offset, x, y in _etc_pixels(layout):
        rgb_offset = offset + 8 if has_alpha else offset
        original_word = word = int.from_bytes(pixels[rgb_offset:rgb_offset + 8], "little")
        colors = _etc_colors(word)
        flip = bool(word & (1 << 32))
        for dy in range(min(4, layout.height - y)):
            for dx in range(min(4, layout.width - x)):
                start = ((y + dy) * layout.width + x + dx) * 4
                index = dx * 4 + dy
                rgb, a = rgba[start:start + 3], rgba[start + 3]
                if rgb != old[start:start + 3]:
                    candidates = colors[(dy if flip else dx) // 2]
                    if rgb not in candidates:
                        raise UnsupportedBclim("ETC1 RGB edit cannot be represented by the original block codebook")
                    selector = candidates.index(rgb)
                    word &= ~((1 << index) | (1 << (index + 16)))
                    word |= ((selector & 1) << index) | ((selector >> 1) << (index + 16))
                if a != old[start + 3]:
                    if not has_alpha or a % 17:
                        raise UnsupportedBclim("ETC1 alpha is opaque; ETC1A4 edits require exact four-bit alpha")
                    _write_nibble(pixels, offset * 2 + index, a // 17)
        if word != original_word:
            pixels[rgb_offset:rgb_offset + 8] = word.to_bytes(8, "little")


def encode_bclim(rgba: bytes, width: int, height: int, template: bytes) -> bytes:
    layout = bclim_layout(template)
    if (width, height) != (layout.width, layout.height) or len(rgba) != width * height * 4:
        raise ValueError("PNG dimensions/RGBA length do not match the source BCLIM")
    old = _decode(template, layout)
    if rgba == old:
        return template

    pixels = bytearray(template)
    fmt = layout.format
    if fmt in ETC_FORMATS:
        _encode_etc(pixels, rgba, old, layout)
    else:
        palette = _palette_colors(template, layout)
        colors = {color: index for index, color in reversed(list(enumerate(palette)))}
        indices_offset = 4 + 2 * len(palette)
        pixel_size = BITS_PER_TEXEL[fmt] // 8
        for index, src in _texels(layout):
            color = rgba[src:src + 4]
            if color == old[src:src + 4]:
                continue
            if palette:
                if color not in colors:
                    raise ValueError("XY RGB5A1 edit requires an existing palette color")
                if len(palette) <= 16:
                    _write_nibble(pixels, indices_offset * 2 + index, colors[color], high_first=True)
                else:
                    pixels[indices_offset + index] = colors[color]
            elif fmt in (12, 13):
                channel = color[0] if fmt == 12 else color[3]
                _write_nibble(pixels, index, channel // 17)
            else:
                dst = index * pixel_size
                pixels[dst:dst + pixel_size] = _encode_direct(color, fmt)

    rebuilt = bytes(pixels)
    # Keep the legacy RGBA4444 quantization contract. All new encoders require
    # an exact decoded match, including implicit channels and hidden RGB.
    if fmt != 8 and decode_bclim(rebuilt)[3] != rgba:
        raise ValueError(f"BCLIM format {fmt} cannot represent the edited RGBA samples exactly")
    return rebuilt


def recompress_bclim_etc(rgba: bytes, template: bytes, edit_mask: bytes) -> tuple[bytes, dict]:
    """Recompress changed blocks while retaining exact alpha and protected samples."""
    from src.rebuilding.etc1_encoding import compress_rgb_block, selector_only

    layout = bclim_layout(template)
    width, height = layout.width, layout.height
    if layout.format not in ETC_FORMATS or len(rgba) != width * height * 4 or len(edit_mask) != width * height:
        raise ValueError("ETC1 recompression requires matching source dimensions and edit mask")
    old = _decode(template, layout)
    for i, allowed in enumerate(edit_mask):
        if not allowed and rgba[4 * i:4 * i + 4] != old[4 * i:4 * i + 4]:
            raise ValueError("ETC1 requested edit touches protected texels")

    pixels = bytearray(template)
    has_alpha = layout.format == 11
    for offset, x, y in _etc_pixels(layout):
        rgb_offset = offset + 8 if has_alpha else offset
        word = int.from_bytes(template[rgb_offset:rgb_offset + 8], "little")
        colors = _etc_colors(word)
        samples = []
        rgb_changed = False
        for i in range(16):
            dx, dy = divmod(i, 4)
            if x + dx >= width or y + dy >= height:
                selector = (word >> i & 1) | (word >> (i + 15) & 2)
                color = colors[(dy if word & (1 << 32) else dx) // 2][selector]
                samples.append((tuple(color), True))
                continue
            idx = (y + dy) * width + x + dx
            pos = idx * 4
            rgb, alpha = rgba[pos:pos + 3], rgba[pos + 3]
            samples.append((tuple(rgb), not edit_mask[idx] or rgb == old[pos:pos + 3]))
            rgb_changed |= rgb != old[pos:pos + 3]
            if alpha != old[pos + 3]:
                if not has_alpha or alpha % 17:
                    raise ValueError("ETC1A4 requires exact four-bit alpha and ETC1 is opaque")
                _write_nibble(pixels, offset * 2 + i, alpha // 17)
        if rgb_changed:
            exact = selector_only(word, tuple(samples))
            if exact is None:
                exact = compress_rgb_block(tuple(samples))
            pixels[rgb_offset:rgb_offset + 8] = exact.to_bytes(8, "little")

    rebuilt = bytes(pixels)
    decoded = _decode(rebuilt, layout)
    changed = 0
    maximum = squared = 0
    for i, allowed in enumerate(edit_mask):
        pos = i * 4
        if decoded[pos + 3] != rgba[pos + 3] or (not allowed and decoded[pos:pos + 4] != old[pos:pos + 4]):
            raise ValueError("ETC1 round trip changed alpha or protected texels")
        if rgba[pos:pos + 3] != old[pos:pos + 3]:
            changed += 1
            errors = [abs(a - b) for a, b in zip(decoded[pos:pos + 3], rgba[pos:pos + 3])]
            maximum = max(maximum, *errors)
            squared += sum(error * error for error in errors)
        elif decoded[pos:pos + 3] != old[pos:pos + 3]:
            raise ValueError("ETC1 round trip drifted outside the edited RGB samples")
    rms = (squared / (3 * changed)) ** 0.5 if changed else 0.0
    if maximum > 12 or rms > 5:
        raise ValueError(f"ETC1 edited RGB exceeds quality limits (max {maximum}, RMS {rms:.2f})")
    return (rebuilt if rebuilt != template else template), {"max_rgb_error": maximum, "rms_rgb_error": round(rms, 3)}
