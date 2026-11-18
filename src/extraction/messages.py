"""Lossless reader for Pokémon Gen VI TextFile records."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct


class MessageError(ValueError):
    """Raised for malformed Gen VI TextFile data."""


@dataclass(frozen=True)
class MessageLine:
    message_id: int
    encrypted_words: tuple[int, ...]
    decoded_words: tuple[int, ...]
    display_text: str
    tokens: tuple[dict[str, object], ...]


def _rol16(value: int, count: int = 3) -> int:
    return ((value << count) | (value >> (16 - count))) & 0xFFFF


def _display(units: tuple[int, ...]) -> tuple[str, tuple[dict[str, object], ...]]:
    output: list[str] = []
    tokens: list[dict[str, object]] = []
    i = 0
    while i < len(units):
        value = units[i]
        if value == 0:
            break
        if value == 0x000A:
            output.append("\\n")
            tokens.append({"type": "newline", "unit": value})
            i += 1
        elif value == 0x0010:
            if i + 2 >= len(units):
                raise MessageError("Truncated variable/control sequence")
            count = units[i + 1]
            if count < 1 or i + 1 + count >= len(units):
                raise MessageError("Invalid variable/control sequence length")
            args = list(units[i + 3:i + 1 + count])
            code = units[i + 2]
            token: dict[str, object] = {"type": "variable", "count": count, "code": code, "args": args}
            if code == 0xBE00:
                display = "\\r"
                token["type"] = "text_return"
            elif code == 0xBE01:
                display = "\\c"
                token["type"] = "text_clear"
            elif code == 0xBE02 and args:
                display = f"[WAIT {args[0]}]"
                token["type"] = "wait"
            elif code == 0xBDFF and args:
                display = f"[~ {args[0]}]"
                token["type"] = "empty_line"
            else:
                rendered_args = ",".join(f"{arg:04X}" for arg in args)
                display = f"[VAR {code:04X}{'(' + rendered_args + ')' if args else ''}]"
            output.append(display)
            tokens.append(token)
            i += 2 + count
        elif value == 0x005C:
            output.append("\\\\")
            tokens.append({"type": "escape", "unit": value})
            i += 1
        elif value in (0xE07F, 0xE08D, 0xE08E, 0xE08F):
            mapped = {0xE07F: "\u202f", 0xE08D: "…", 0xE08E: "♂", 0xE08F: "♀"}[value]
            output.append(mapped)
            tokens.append({"type": "remapped_character", "unit": value, "display": mapped})
            i += 1
        elif 0xE000 <= value <= 0xF8FF:
            output.append(f"[U+{value:04X}]")
            tokens.append({"type": "private_use_character", "unit": value})
            i += 1
        else:
            output.append(chr(value))
            i += 1
    return "".join(output), tuple(tokens)


@dataclass(frozen=True)
class TextFile:
    raw: bytes
    lines: tuple[MessageLine, ...]
    source_sha256: str

    @classmethod
    def parse(cls, raw: bytes) -> "TextFile":
        if len(raw) < 0x14:
            raise MessageError("TextFile is shorter than its header")
        section_count, line_count, total_length, initial_key, section_offset = struct.unpack_from("<HHIII", raw, 0)
        if section_count != 1 or initial_key != 0 or section_offset != 0x10 or section_offset + total_length != len(raw):
            raise MessageError("Unsupported or inconsistent TextFile header")
        section_length = struct.unpack_from("<I", raw, section_offset)[0]
        if section_length != total_length:
            raise MessageError("TextFile section length mismatch")
        table_start = section_offset + 4
        table_end = table_start + 8 * line_count
        if table_end > len(raw):
            raise MessageError("TextFile line table exceeds file bounds")
        records: list[tuple[int, int]] = []
        for line_id in range(line_count):
            record = table_start + line_id * 8
            relative_offset = struct.unpack_from("<I", raw, record)[0]
            length_words = struct.unpack_from("<H", raw, record + 4)[0]
            absolute_offset = section_offset + relative_offset
            if relative_offset < (table_end - section_offset) or absolute_offset + 2 * length_words > len(raw):
                raise MessageError(f"Line {line_id} data is outside TextFile bounds")
            records.append((absolute_offset, length_words))
        lines: list[MessageLine] = []
        key = 0x7C89
        for message_id, (offset, count) in enumerate(records):
            encrypted = struct.unpack_from(f"<{count}H", raw, offset) if count else ()
            decoded = []
            current_key = key
            for word in encrypted:
                decoded.append(word ^ current_key)
                current_key = _rol16(current_key)
            decoded_tuple = tuple(decoded)
            display, tokens = _display(decoded_tuple)
            lines.append(MessageLine(message_id, tuple(encrypted), decoded_tuple, display, tokens))
            key = (key + 0x2983) & 0xFFFF
        return cls(raw, tuple(lines), hashlib.sha256(raw).hexdigest())


def rebuild_identity(text_file: TextFile) -> bytes:
    """Return the exact original structure after verifying each line still matches its source bytes."""
    reparsed = TextFile.parse(text_file.raw)
    if reparsed.lines != text_file.lines or reparsed.source_sha256 != text_file.source_sha256:
        raise MessageError("TextFile identity validation failed")
    return text_file.raw
