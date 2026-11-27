"""Read-only XY BCH metadata and PICA surface extraction."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from itertools import pairwise
import struct

from src.rebuilding.bclim import BITS_PER_TEXEL, decode_tiled_rgba


MAGIC = b"BCH\0"
XY_VERSION = (7, 7, 38669)
SECTION_NAMES = ("contents", "strings", "commands", "data", "relocations")
RESOURCE_TYPES = (
    "models", "materials", "shaders", "textures", "lookup_tables", "lights", "cameras", "fogs",
    "skeletal_animations", "material_animations", "visibility_animations", "light_animations",
    "camera_animations", "fog_animations", "scenes",
)
PICA_FORMATS = ("RGBA8", "RGB8", "RGB5A1", "RGB565", "RGBA4", "LA8", "HILO8",
                "L8", "A8", "LA4", "L4", "A4", "ETC1", "ETC1A4")
PICA_TO_BCLIM = (9, 6, 7, 5, 8, 3, 4, 0, 1, 2, 12, 13, 10, 11)
FACE_NAMES = ("+X", "-X", "+Y", "-Y", "+Z", "-Z")


class UnsupportedBch(ValueError):
    """An unverified BCH version or feature."""


@dataclass(frozen=True)
class Section:
    offset: int
    length: int

    @property
    def end(self) -> int:
        return self.offset + self.length

    def contains(self, offset: int, length: int) -> bool:
        return self.offset <= offset and offset + length <= self.end


@dataclass(frozen=True)
class Relocation:
    flag: int
    section: str
    target: int


@dataclass(frozen=True)
class Surface:
    face: str
    mip_level: int
    width: int
    height: int
    data_offset: int
    data_length: int


@dataclass(frozen=True)
class Texture:
    index: int
    name: str
    descriptor_offset: int
    format: int
    mipmap_count: int
    address_fields: tuple[int, ...]
    surfaces: tuple[Surface, ...]


@dataclass
class Bch:
    version: tuple[int, int, int]
    sections: dict[str, Section]
    resource_counts: dict[str, int]
    relocations: dict[int, Relocation]
    textures: list[Texture]
    issues: list[dict]


def _read_sections(raw: bytes) -> tuple[tuple[int, int, int], dict[str, Section]]:
    if raw[:4] != MAGIC:
        raise ValueError("Invalid BCH signature")
    if len(raw) < 8:
        raise ValueError("Truncated BCH version")
    version = struct.unpack_from("<BBH", raw, 4)
    if version != XY_VERSION:
        raise UnsupportedBch(f"Unsupported BCH compatibility/converter version {version}")
    if len(raw) < 56:
        raise ValueError("Truncated XY BCH header")
    offsets = struct.unpack_from("<5I", raw, 8)
    lengths = struct.unpack_from("<5I", raw, 28)
    sections = {}
    end = 56
    for name, offset, length in zip(SECTION_NAMES, offsets, lengths):
        if offset < end or offset + length > len(raw):
            raise ValueError(f"BCH {name} section is out of bounds or overlaps the preceding section")
        sections[name] = Section(offset, length)
        end = offset + length
    if end != len(raw) or sections["relocations"].length % 4:
        raise ValueError("BCH relocation table has invalid length or trailing data")
    return version, sections


def _read_relocations(raw: bytes, sections: dict[str, Section]) -> dict[int, Relocation]:
    # GPU relocation values are disk byte offsets. VRAM address units and the
    # index-width bit only matter to the runtime loader.
    rules = {
        0: ("contents", "contents"), 1: ("contents", "strings"), 2: ("contents", "commands"),
        3: ("contents", "commands"),
        0x24: ("commands", "data"), 0x25: ("commands", "data"), 0x26: ("commands", "data"),
        0x27: ("commands", "data"), 0x28: ("commands", "data"),
    }
    table = sections["relocations"]
    relocations = {}
    for (entry,) in struct.iter_unpack("<I", raw[table.offset:table.end]):
        flag = entry >> 25
        if flag not in rules:
            raise UnsupportedBch(f"Unsupported XY BCH relocation flag 0x{flag:x}")
        source_name, target_name = rules[flag]
        source, target = sections[source_name], sections[target_name]
        location = source.offset + (entry & 0x1FFFFFF) * (1 if flag == 1 else 4)
        if not source.contains(location, 4) or location in relocations:
            raise ValueError("BCH relocation source is out of bounds or duplicated")
        relative = struct.unpack_from("<I", raw, location)[0]
        absolute = target.offset + relative
        slot = location - source.offset
        # An empty dictionary may use the end of contents as its zero-length list.
        empty_list = (flag == 0 and slot < 12 * len(RESOURCE_TYPES) and slot % 12 == 0
                      and absolute == target.end and source.contains(location + 4, 4)
                      and struct.unpack_from("<I", raw, location + 4)[0] == 0)
        if not target.contains(absolute, 1) and not empty_list:
            raise ValueError(f"BCH relocation target is outside {target_name}")
        relocations[location] = Relocation(flag, target_name, absolute)
    if any(right - left < 4 for left, right in pairwise(sorted(relocations))):
        raise ValueError("BCH relocation fields overlap")
    return relocations


def _pointer(relocations: dict[int, Relocation], location: int, section: str) -> Relocation:
    pointer = relocations.get(location)
    if pointer is None or pointer.section != section:
        raise ValueError(f"BCH field at 0x{location:x} has no {section} relocation")
    return pointer


def _dictionary_tables(raw: bytes, contents: Section, relocations: dict[int, Relocation]):
    if contents.length < len(RESOURCE_TYPES) * 12:
        raise ValueError("Truncated BCH resource directory")
    for index, kind in enumerate(RESOURCE_TYPES):
        slot = contents.offset + index * 12
        table_rel, count, tree_rel = struct.unpack_from("<III", raw, slot)
        if table_rel or count or slot in relocations:
            table = _pointer(relocations, slot, "contents").target
            if not contents.contains(table, count * 4):
                raise ValueError(f"BCH {kind} pointer table exceeds contents")
        else:
            table = 0
        if tree_rel or slot + 8 in relocations:
            tree = _pointer(relocations, slot + 8, "contents").target
            if not contents.contains(tree, 12 * (count + 1)):
                raise ValueError(f"BCH {kind} name tree exceeds contents")
        yield kind, table, count


def _commands(raw: bytes, start: int, words: int, section: Section):
    if words == 0 or words % 2 or not section.contains(start, words * 4):
        raise ValueError("Invalid BCH PICA command list bounds")
    end = start + words * 4
    cursor = start
    while cursor < end:
        header = struct.unpack_from("<I", raw, cursor + 4)[0]
        register = header & 0xFFFF
        mask = (header >> 16) & 15
        extra = (header >> 20) & 0x7FF
        next_packet = cursor + ((extra + 3) & ~1) * 4
        if next_packet > end:
            raise ValueError("Truncated BCH PICA command packet")
        for index in range(extra + 1):
            location = cursor if index == 0 else cursor + (index + 1) * 4
            value = struct.unpack_from("<I", raw, location)[0]
            yield register + (index if header >> 31 else 0), mask, value, location
        cursor = next_packet


def _texture_registers(raw: bytes, descriptor: int, section: Section, relocations: dict[int, Relocation],
                       unit: int) -> dict[int, tuple[int, int]]:
    field = descriptor + unit * 8
    relative, words = struct.unpack_from("<II", raw, field)
    if words == 0 and unit and not relative and field not in relocations:
        return {}
    start = _pointer(relocations, field, "commands").target
    relevant = ({0x82, 0x83, 0x84, 0x8E, *range(0x85, 0x8B)}, {0x92, 0x94, 0x95, 0x96},
                {0x9A, 0x9C, 0x9D, 0x9E})[unit]
    registers = {}
    for register, mask, value, location in _commands(raw, start, words, section):
        if register in relevant:
            if mask != 15 or register in registers:
                raise UnsupportedBch("BCH texture uses partial or repeated PICA register writes")
            registers[register] = value, location
    return registers


def _texture(raw: bytes, index: int, pointer_field: int, sections: dict[str, Section],
             relocations: dict[int, Relocation], data_targets: list[int]) -> Texture:
    descriptor = _pointer(relocations, pointer_field, "contents").target
    if not sections["contents"].contains(descriptor, 32):
        raise ValueError("Truncated BCH texture descriptor")
    format_id, mipmaps = struct.unpack_from("<BB", raw, descriptor + 24)
    fmt = _pixel_format(format_id)
    if not 1 <= mipmaps <= 8:
        raise UnsupportedBch(f"Unsupported BCH mipmap count {mipmaps}")
    start = _pointer(relocations, descriptor + 28, "strings").target
    end = raw.find(b"\0", start, sections["strings"].end)
    if end <= start:
        raise ValueError("BCH texture name is empty or lacks a terminator")
    name = raw[start:end].decode("utf-8")

    commands = sections["commands"]
    primary = _texture_registers(raw, descriptor, commands, relocations, 0)
    if not {0x82, 0x85, 0x8E} <= primary.keys():
        raise ValueError("BCH texture is missing PICA dimensions, address or format")
    if primary[0x8E][0] != format_id:
        raise ValueError("BCH descriptor format differs from PICA format")
    dim = primary[0x82][0]
    width, height = (dim >> 16) & 0x7FF, dim & 0x7FF
    if dim != ((width << 16) | height) or any(
        size < 8 or size > 1024 or size & (size - 1) for size in (width, height)
    ):
        raise UnsupportedBch("BCH texture uses an unsupported PICA dimension")
    _check_lod(primary, 0x84, mipmaps)

    face_registers = [reg for reg in range(0x85, 0x8B) if reg in primary]
    if len(face_registers) not in (1, 6) or (len(face_registers) == 6 and width != height):
        raise UnsupportedBch("BCH texture has an incomplete or non-square cubemap")
    if 0x83 in primary:
        mode = (primary[0x83][0] >> 28) & 7
        if mode != (1 if len(face_registers) == 6 else 0):
            raise UnsupportedBch("Unsupported BCH texture sampling mode")

    address_fields = []
    surfaces = []
    for face_index, register in enumerate(face_registers):
        field = primary[register][1]
        pointer = _pointer(relocations, field, "data")
        if pointer.flag != (0x25 if face_index else 0x24) or pointer.target % 8:
            raise ValueError("Invalid BCH texture address relocation")
        address_fields.append(field)
        face = FACE_NAMES[face_index] if len(face_registers) == 6 else "2D"
        surfaces.extend(_mip_surfaces(sections["data"], pointer.target, face, width, height, fmt, mipmaps))

    for unit, registers in enumerate(((0x92, 0x94, 0x95, 0x96), (0x9A, 0x9C, 0x9D, 0x9E)), 1):
        alt = _texture_registers(raw, descriptor, commands, relocations, unit)
        if not alt:
            continue
        dim_reg, lod_reg, addr_reg, fmt_reg = registers
        if not {dim_reg, addr_reg, fmt_reg} <= alt.keys():
            raise ValueError("Incomplete BCH alternate texture-unit commands")
        field = alt[addr_reg][1]
        pointer = _pointer(relocations, field, "data")
        if (alt[dim_reg][0], alt[fmt_reg][0], pointer.flag, pointer.target) != (
            dim, format_id, 0x24, surfaces[0].data_offset
        ):
            raise UnsupportedBch("BCH alternate texture unit references a different surface")
        _check_lod(alt, lod_reg, mipmaps)
        address_fields.append(field)
    for surface in surfaces:
        following = bisect_right(data_targets, surface.data_offset)
        if following < len(data_targets) and data_targets[following] < surface.data_offset + surface.data_length:
            raise ValueError("BCH texture surface spans another relocated data target")
    return Texture(index, name, descriptor, format_id, mipmaps, tuple(address_fields), tuple(surfaces))


def _check_lod(registers: dict[int, tuple[int, int]], register: int, mipmaps: int) -> None:
    lod = registers.get(register)
    if lod is None:
        if mipmaps > 1:
            raise UnsupportedBch("BCH mip chain has no PICA LOD declaration")
    elif ((lod[0] >> 16) & 15) != mipmaps - 1 or ((lod[0] >> 24) & 15):
        raise UnsupportedBch("BCH mipmap count differs from PICA LOD range")


def _mip_surfaces(data: Section, offset: int, face: str, width: int, height: int,
                  fmt: int, count: int):
    for level in range(count):
        if min(width, height) < 8:
            raise UnsupportedBch("BCH mip chain contains levels smaller than a PICA tile")
        length = width * height * BITS_PER_TEXEL[fmt] // 8
        if not data.contains(offset, length):
            raise ValueError("BCH texture surface exceeds the data section")
        yield Surface(face, level, width, height, offset, length)
        offset += length
        width //= 2
        height //= 2


def _pixel_format(format_id: int) -> int:
    if not 0 <= format_id < len(PICA_TO_BCLIM):
        raise UnsupportedBch(f"Unsupported BCH PICA format {format_id}")
    return PICA_TO_BCLIM[format_id]


def parse_bch(raw: bytes) -> Bch:
    version, sections = _read_sections(raw)
    relocations = _read_relocations(raw, sections)
    data_targets = sorted({p.target for p in relocations.values() if p.section == "data"})
    counts = {}
    textures = []
    issues = []
    for kind, table, count in _dictionary_tables(raw, sections["contents"], relocations):
        counts[kind] = count
        for index in range(count):
            field = table + index * 4
            if kind != "textures":
                _pointer(relocations, field, "contents")
                continue
            try:
                textures.append(_texture(raw, index, field, sections, relocations, data_targets))
            except ValueError as exc:
                issues.append({"texture_index": index, "status": "unsupported" if isinstance(exc, UnsupportedBch)
                               else "failed", "reason": str(exc)})
    return Bch(version, sections, counts, relocations, textures, issues)


def decode_surface(payload: bytes, surface: Surface, format_id: int) -> bytes:
    rgba = decode_tiled_rgba(payload, surface.width, surface.height, _pixel_format(format_id))
    # BCH stores images in PICA's bottom-up UV convention.
    stride = surface.width * 4
    return b"".join(rgba[end - stride:end] for end in range(len(rgba), 0, -stride))


def replace_isolated_texture(raw: bytes, index: int, replacement: bytes) -> bytes:
    """Replace an owned 2D base-level payload in an otherwise texture-only BCH."""
    bch = parse_bch(raw)
    if bch.issues or any(count for kind, count in bch.resource_counts.items() if kind != "textures"):
        raise UnsupportedBch("BCH replacement requires a fully understood texture-only container")
    texture = next((entry for entry in bch.textures if entry.index == index), None)
    if texture is None or len(texture.surfaces) != 1:
        raise UnsupportedBch("BCH replacement requires one 2D base-level surface")
    surface, = texture.surfaces
    start, end = surface.data_offset, surface.data_offset + surface.data_length
    if len(replacement) != surface.data_length:
        raise ValueError("BCH replacement must have the original byte length")
    for other in bch.textures:
        for region in other.surfaces:
            if other is not texture and region.data_offset < end and start < region.data_offset + region.data_length:
                raise UnsupportedBch("BCH replacement region overlaps another surface")
    owned = {field for entry in bch.textures for field in entry.address_fields}
    for field, pointer in bch.relocations.items():
        if pointer.section == "data" and (field not in owned
                or (start <= pointer.target < end and field not in texture.address_fields)):
            raise UnsupportedBch("BCH replacement found another data reference")
    decode_surface(replacement, surface, texture.format)
    return raw if replacement == raw[start:end] else raw[:start] + replacement + raw[end:]
