"""Strict reader/rebuilder for Nintendo 3DS Gen VI GARC version 4 archives."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct


class GARCError(ValueError):
    """Raised when an archive violates the supported GARC v4 layout."""


@dataclass(frozen=True)
class Member:
    entry_id: int
    subfile_id: int
    data: bytes
    start: int
    padded_end: int


@dataclass(frozen=True)
class Entry:
    vector: int
    members: tuple[Member, ...]


def _u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


@dataclass
class GARC:
    """Parsed Gen VI GARC v4 retaining the metadata prefix for stable rebuilds."""

    raw: bytes
    data_offset: int
    file_size_header: int
    largest_member_header: int
    fato_start: int
    fato_end: int
    fatb_start: int
    fatb_end: int
    fimg_start: int
    fimg_data_size: int
    entries: list[Entry]
    members: list[Member]

    @classmethod
    def parse(cls, raw: bytes) -> "GARC":
        if len(raw) < 0x1C or raw[:4] != b"CRAG":
            raise GARCError("Missing Gen VI GARC signature (CRAG)")
        header_len, bom, version, chunk_count, data_offset, file_size, largest = struct.unpack_from("<IHHIIII", raw, 4)
        if (header_len, bom, version, chunk_count) != (0x1C, 0xFEFF, 0x0400, 4):
            raise GARCError(f"Unsupported GARC header: header={header_len:#x}, bom={bom:#x}, version={version:#x}, chunks={chunk_count}")
        if file_size != len(raw):
            raise GARCError(f"Header file size {file_size} does not match actual size {len(raw)}")
        if data_offset < 0x1C or data_offset >= len(raw):
            raise GARCError("Data offset is outside archive")

        pos = 0x1C
        if raw[pos:pos + 4] != b"OTAF":
            raise GARCError("Missing FATO/OTAF section")
        fato_size = _u32(raw, pos + 4)
        entry_count = _u16(raw, pos + 8)
        fato_end = pos + fato_size
        if fato_size != 12 + 4 * entry_count or fato_end > data_offset:
            raise GARCError("Invalid FATO section length")
        fato_start = pos
        fato_offsets = [_u32(raw, pos + 12 + i * 4) for i in range(entry_count)]

        pos = fato_end
        if raw[pos:pos + 4] != b"BTAF":
            raise GARCError("Missing FATB/BTAF section")
        fatb_size = _u32(raw, pos + 4)
        reported_files = _u32(raw, pos + 8)
        fatb_end = pos + fatb_size
        if fatb_end > data_offset or fatb_size < 12:
            raise GARCError("Invalid FATB section bounds")
        fatb_start = pos
        entries: list[Entry] = []
        members: list[Member] = []
        q = pos + 12
        total_members = 0
        for entry_id in range(entry_count):
            if q + 4 > fatb_end:
                raise GARCError("FATB entry header exceeds section")
            vector = _u32(raw, q)
            q += 4
            expected_fato_offset = q - (pos + 12) - 4
            if fato_offsets[entry_id] != expected_fato_offset:
                raise GARCError(f"FATO entry {entry_id} offset mismatch")
            row_members: list[Member] = []
            for sub_id in range(32):
                if vector & (1 << sub_id):
                    if q + 12 > fatb_end:
                        raise GARCError("FATB member descriptor exceeds section")
                    start, end, length = struct.unpack_from("<III", raw, q)
                    q += 12
                    if not (start <= end and length <= end - start and data_offset + end <= len(raw)):
                        raise GARCError(f"Invalid data bounds for entry {entry_id}/{sub_id}")
                    member = Member(entry_id, sub_id, raw[data_offset + start:data_offset + start + length], start, end)
                    row_members.append(member)
                    members.append(member)
                    total_members += 1
            entries.append(Entry(vector, tuple(row_members)))
        if q != fatb_end:
            raise GARCError("FATB section has unexpected trailing bytes")

        pos = fatb_end
        if raw[pos:pos + 4] != b"BMIF" or pos + 12 > data_offset:
            raise GARCError("Missing FIMG/BMIF section")
        fimg_size = _u32(raw, pos + 4)
        fimg_data_size = _u32(raw, pos + 8)
        if fimg_size != 12 or pos + fimg_size != data_offset:
            raise GARCError("Invalid FIMG section size or data offset")
        if fimg_data_size != len(raw) - data_offset:
            raise GARCError("FIMG data size does not match archive tail")
        if reported_files not in (total_members, entry_count):
            raise GARCError(f"FATB file count {reported_files} matches neither entries ({entry_count}) nor members ({total_members})")
        return cls(raw, data_offset, file_size, largest, fato_start, fato_end, fatb_start, fatb_end, pos, fimg_data_size, entries, members)

    def rebuild(self, replacement: dict[tuple[int, int], bytes] | None = None) -> bytes:
        """Rebuild v4 layout, preserving the exact metadata prefix and member vectors."""
        replacement = replacement or {}
        known = {(m.entry_id, m.subfile_id) for m in self.members}
        if replacement.keys() - known:
            raise GARCError("Replacement refers to an absent member")
        prefix = bytearray(self.raw[:self.data_offset])
        data = bytearray()
        largest = 0
        q = self.fatb_start + 12
        for entry in self.entries:
            q += 4
            for member in entry.members:
                blob = replacement.get((member.entry_id, member.subfile_id), member.data)
                start = len(data)
                data.extend(blob)
                pad_len = (-len(data)) % 4
                data.extend(b"\xff" * pad_len)
                end = len(data)
                struct.pack_into("<III", prefix, q, start, end, len(blob))
                q += 12
                largest = max(largest, len(blob))
        output = prefix + data
        struct.pack_into("<I", output, 0x10, self.data_offset)
        struct.pack_into("<I", output, 0x14, len(output))
        struct.pack_into("<I", output, 0x18, largest)
        struct.pack_into("<I", output, self.fimg_start + 8, len(data))
        return bytes(output)


def extract(archive_path: Path, output_dir: Path) -> dict[str, object]:
    """Extract raw members (no implicit decompression) and write provenance JSONL."""
    source = archive_path.resolve(strict=True)
    output = output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = GARC.parse(source.read_bytes())
    manifest = []
    for member in archive.members:
        rel = f"{member.entry_id:04d}_{member.subfile_id:02d}.bin"
        (output / rel).write_bytes(member.data)
        manifest.append({
            "archive": source.as_posix(), "entry_id": member.entry_id, "subfile_id": member.subfile_id,
            "output": rel, "size": len(member.data), "sha256": hashlib.sha256(member.data).hexdigest(),
            "compressed_lz11": member.data[:1] == b"\x11",
        })
    manifest_path = output / "manifest.jsonl"
    manifest_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in manifest), encoding="utf-8", newline="\n")
    return {"archive": source.as_posix(), "entries": len(archive.entries), "members": len(archive.members), "output": output.as_posix(), "manifest": manifest_path.as_posix()}
