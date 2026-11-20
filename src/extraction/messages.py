"""Reader and lossless serializer for Pokemon Gen VI TextFile records."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from collections.abc import Mapping, Sequence


class MessageError(ValueError):
    """Raised for malformed or unsafe Gen VI TextFile data."""


@dataclass(frozen=True)
class MessageLine:
    message_id: int
    relative_offset: int
    table_reserved: int
    padding_after: bytes
    encrypted_words: tuple[int, ...]
    decoded_words: tuple[int, ...]
    display_text: str
    tokens: tuple[dict[str, object], ...]
    terminator_suffix: tuple[int, ...]


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
            end = i + 2 + count
            if count < 1 or end > len(units):
                raise MessageError("Invalid variable/control sequence length")
            args = list(units[i + 3:end])
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
            i = end
        elif value == 0x005C:
            output.append("\\\\")
            tokens.append({"type": "escape", "unit": value})
            i += 1
        elif value in (0xE07F, 0xE08D, 0xE08E, 0xE08F):
            mapped = {0xE07F: "\u202f", 0xE08D: "\u2026", 0xE08E: "\u2642", 0xE08F: "\u2640"}[value]
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


def _terminator_index(units: tuple[int, ...]) -> int:
    """Find the line terminator outside length-prefixed variable arguments."""
    i = 0
    while i < len(units):
        value = units[i]
        if value == 0:
            return i
        if value == 0x0010:
            if i + 2 >= len(units):
                raise MessageError("Truncated variable/control sequence before terminator")
            count = units[i + 1]
            end = i + 2 + count
            if count < 1 or end > len(units):
                raise MessageError("Invalid variable/control sequence before terminator")
            i = end
        else:
            i += 1
    # Some observed Gen VI records end exactly after a complete control event
    # (for example 0010 0002 BDFF 0000) without a separate terminator word.
    # Preserve these records byte-for-byte, but replacement remains disabled
    # because there is no source terminator suffix to retain.
    return len(units)


def _encode_words(words: Sequence[int], initial_key: int) -> tuple[int, ...]:
    key = initial_key
    encrypted = []
    for word in words:
        if not 0 <= word <= 0xFFFF:
            raise MessageError(f"UTF-16 word is out of range: {word}")
        encrypted.append(word ^ key)
        key = _rol16(key)
    return tuple(encrypted)


def _control_signature(words: tuple[int, ...]) -> tuple[dict[str, object], ...]:
    return _display(words)[1]


@dataclass(frozen=True)
class TextFile:
    raw: bytes
    lines: tuple[MessageLine, ...]
    source_sha256: str
    header_prefix: bytes
    section_offset: int
    section_header: bytes
    table_padding: bytes

    @classmethod
    def parse(cls, raw: bytes) -> "TextFile":
        if len(raw) < 0x14:
            raise MessageError("TextFile is shorter than its header")
        section_count, line_count, total_length, initial_key, section_offset = struct.unpack_from("<HHIII", raw, 0)
        if section_count != 1 or initial_key != 0 or section_offset != 0x10 or section_offset + total_length != len(raw):
            raise MessageError("Unsupported or inconsistent TextFile header")
        section_header = raw[section_offset:section_offset + 4]
        section_length = struct.unpack("<I", section_header)[0]
        if section_length != total_length:
            raise MessageError("TextFile section length mismatch")
        table_start = section_offset + 4
        table_end = table_start + 8 * line_count
        if table_end > len(raw):
            raise MessageError("TextFile line table exceeds file bounds")
        table: list[tuple[int, int, int]] = []
        for message_id in range(line_count):
            record = table_start + message_id * 8
            relative_offset, length_words, reserved = struct.unpack_from("<IHH", raw, record)
            absolute_offset = section_offset + relative_offset
            if relative_offset < table_end - section_offset or absolute_offset + 2 * length_words > len(raw):
                raise MessageError(f"Line {message_id} data is outside TextFile bounds")
            table.append((relative_offset, length_words, reserved))

        absolute_spans = [(section_offset + offset, section_offset + offset + 2 * count) for offset, count, _ in table]
        if absolute_spans != sorted(absolute_spans):
            raise MessageError("TextFile message data is not in message-ID order")
        for previous, current in zip(absolute_spans, absolute_spans[1:]):
            if previous[1] > current[0]:
                raise MessageError("TextFile message data overlaps")

        first_data = absolute_spans[0][0] if absolute_spans else table_end
        table_padding = raw[table_end:first_data]
        lines: list[MessageLine] = []
        key = 0x7C89
        for message_id, (relative_offset, count, reserved) in enumerate(table):
            start = section_offset + relative_offset
            end = start + 2 * count
            padding_end = absolute_spans[message_id + 1][0] if message_id + 1 < line_count else len(raw)
            padding_after = raw[end:padding_end]
            encrypted = struct.unpack_from(f"<{count}H", raw, start) if count else ()
            decoded = []
            current_key = key
            for word in encrypted:
                decoded.append(word ^ current_key)
                current_key = _rol16(current_key)
            decoded_tuple = tuple(decoded)
            display, tokens = _display(decoded_tuple)
            try:
                terminal = _terminator_index(decoded_tuple)
            except MessageError as exc:
                raise MessageError(f"Message {message_id}: {exc}") from exc
            lines.append(MessageLine(
                message_id, relative_offset, reserved, padding_after, tuple(encrypted), decoded_tuple,
                display, tokens, decoded_tuple[terminal:],
            ))
            key = (key + 0x2983) & 0xFFFF
        return cls(
            raw, tuple(lines), hashlib.sha256(raw).hexdigest(), raw[:section_offset],
            section_offset, section_header, table_padding,
        )

    def rebuild(self, replacements: Mapping[int, str | Sequence[int]] | None = None, *,
                control_adjustments: Mapping[int, Sequence[Sequence[int]]] | None = None) -> bytes:
        """Serialize the original file, optionally replacing messages by stable line ID.

        String replacements encode as BMP UTF-16 code units. Sequence replacements
        provide decoded message-body words (without the original terminator suffix).
        Both forms must preserve the exact source control/placeholder token sequence,
        unless a caller supplies a narrowly scoped explicit control adjustment.
        """
        replacements = replacements or {}
        control_adjustments = control_adjustments or {}
        if any(not isinstance(message_id, int) or message_id < 0 or message_id >= len(self.lines) for message_id in replacements):
            raise MessageError("Replacement refers to an absent message ID")
        decoded_records: list[tuple[int, ...]] = []
        for line in self.lines:
            replacement = replacements.get(line.message_id)
            if replacement is None:
                words = line.decoded_words
            else:
                if not line.terminator_suffix:
                    raise MessageError(f"Message {line.message_id} has no terminator to preserve")
                if isinstance(replacement, str):
                    if not replacement:
                        raise MessageError("Empty replacement text is not allowed")
                    words_body = []
                    for character in replacement:
                        codepoint = ord(character)
                        if codepoint > 0xFFFF or 0xD800 <= codepoint <= 0xDFFF:
                            raise MessageError(f"Character U+{codepoint:04X} is not a supported BMP code unit")
                        if codepoint == 0 or (codepoint < 0x20 and codepoint != 0x0A):
                            raise MessageError(f"Control character U+{codepoint:04X} is not allowed in plain text")
                        words_body.append(codepoint)
                    words = tuple(words_body) + line.terminator_suffix
                else:
                    words_body = tuple(replacement)
                    if any(not isinstance(word, int) or not 0 <= word <= 0xFFFF for word in words_body):
                        raise MessageError("Decoded replacement words must be unsigned 16-bit integers")
                    words = words_body + line.terminator_suffix
                expected_tokens = list(line.tokens)
                for event in control_adjustments.get(line.message_id, ()):
                    if tuple(event) != (0x0010, 0x0003, 0x1100, 0x00FF, 0x0202):
                        raise MessageError("Only the documented Gen VI gender-selection control can be removed")
                    gender_token = {"type": "variable", "count": 3, "code": 0x1100, "args": [0x00FF, 0x0202]}
                    try:
                        expected_tokens.remove(gender_token)
                    except ValueError as exc:
                        raise MessageError("Requested control adjustment is absent from the source message") from exc
                if _control_signature(words) != tuple(expected_tokens):
                    raise MessageError(f"Replacement for message {line.message_id} changes control codes or placeholders")
            if len(words) > 0xFFFF:
                raise MessageError(f"Replacement for message {line.message_id} exceeds the TextFile word-count limit")
            decoded_records.append(words)

        table_start = self.section_offset + 4
        table_end = table_start + 8 * len(self.lines)
        output = bytearray(self.header_prefix + self.section_header)
        output.extend(b"\x00" * (8 * len(self.lines)))
        output.extend(self.table_padding)
        key = 0x7C89
        for line, words in zip(self.lines, decoded_records):
            relative_offset = len(output) - self.section_offset
            if relative_offset > 0xFFFFFFFF:
                raise MessageError("Serialized TextFile offset exceeds 32-bit range")
            struct.pack_into("<IHH", output, table_start + line.message_id * 8, relative_offset, len(words), line.table_reserved)
            encrypted = _encode_words(words, key)
            output.extend(struct.pack(f"<{len(encrypted)}H", *encrypted) if encrypted else b"")
            output.extend(line.padding_after)
            key = (key + 0x2983) & 0xFFFF

        section_length = len(output) - self.section_offset
        if section_length > 0xFFFFFFFF:
            raise MessageError("Serialized TextFile exceeds 32-bit length")
        struct.pack_into("<I", output, 4, section_length)
        struct.pack_into("<I", output, self.section_offset, section_length)
        rebuilt = bytes(output)
        reparsed = TextFile.parse(rebuilt)
        if len(reparsed.lines) != len(self.lines):
            raise MessageError("Serialized TextFile message count changed")
        return rebuilt


def rebuild_identity(text_file: TextFile) -> bytes:
    """Perform a true no-change serialization and require byte-exact identity."""
    rebuilt = text_file.rebuild()
    if rebuilt != text_file.raw:
        raise MessageError("TextFile no-change serialization differs from source bytes")
    reparsed = TextFile.parse(rebuilt)
    if reparsed.lines != text_file.lines or reparsed.source_sha256 != text_file.source_sha256:
        raise MessageError("TextFile identity validation failed")
    return rebuilt
