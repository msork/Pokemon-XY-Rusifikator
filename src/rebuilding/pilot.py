"""Apply reviewed translation records to disposable Gen VI archive copies."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unicodedata
from typing import Any

from src.extraction.garc import GARC, GARCError
from src.extraction.messages import MessageError, TextFile


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_variant_hash(words: tuple[int, ...]) -> str:
    return sha256(b"".join(word.to_bytes(2, "little") for word in words))


def parse_record_id(record_id: str) -> tuple[str, int, int, int]:
    match = re.fullmatch(r"gen6:(a(?:/\d+){3}):(\d{4})/(\d{2}):(\d{5})", record_id)
    if match is None:
        raise ValueError(f"Unsupported pilot record ID: {record_id}")
    return match.group(1), int(match.group(2)), int(match.group(3)), int(match.group(4))


def effective_resource(base_path: Path, update_path: Path) -> tuple[Path, str]:
    """Select the update file when present, otherwise base, without merging trees."""
    if update_path.is_file():
        return update_path, "update-1.5"
    if base_path.is_file():
        return base_path, "base"
    raise FileNotFoundError(f"Resource missing from both base and update: {base_path} / {update_path}")


def translation_words(translation: dict[str, Any]) -> tuple[int, ...]:
    segments = translation.get("translation_segments")
    if not isinstance(segments, list):
        raise ValueError("Translation has no segment list")
    words: list[int] = []
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) not in ({"text"}, {"control_words"}):
            raise ValueError("Invalid translation segment")
        if "text" in segment:
            text = segment["text"]
            if not isinstance(text, str) or not text:
                raise ValueError("Translation text segments must be nonempty strings")
            if unicodedata.normalize("NFC", text) != text:
                raise ValueError("Translation text must be NFC-normalized")
            for character in text:
                value = ord(character)
                if value == 0 or value > 0xFFFF or 0xD800 <= value <= 0xDFFF or value < 0x20:
                    raise ValueError(f"Unsupported character U+{value:04X} in translation")
                words.append(value)
        else:
            control_words = segment["control_words"]
            if not isinstance(control_words, list) or not control_words:
                raise ValueError("Control segments must contain words")
            for word in control_words:
                if not isinstance(word, str) or re.fullmatch(r"[0-9A-F]{4}", word) is None:
                    raise ValueError(f"Invalid control word {word!r}")
                words.append(int(word, 16))
    return tuple(words)


def build_archive(source_bytes: bytes, resource: str, game: str, version: str,
                  translations: list[dict[str, Any]], *, include_machine_drafts: bool = False) -> tuple[bytes, dict[str, Any]]:
    archive = GARC.parse(source_bytes)
    if archive.rebuild() != source_bytes:
        raise GARCError(f"Source GARC no-change rebuild is not byte-exact: {resource}")
    replacement_by_member: dict[tuple[int, int], dict[int, tuple[int, ...]]] = {}
    targets: list[tuple[dict[str, Any], int, int, int]] = []
    for row in translations:
        row_resource, entry_id, subfile_id, message_id = parse_record_id(str(row.get("record_id", "")))
        if row.get("scope") not in {"shared", "x", "y"}:
            raise ValueError(f"Invalid game scope: {row.get('record_id')}")
        if row_resource != resource:
            continue
        scope = row.get("scope")
        if scope not in ("shared", "x" if game == "pokemon-x" else "y"):
            continue
        if version not in row.get("version_scope", []):
            continue
        status = row.get("status")
        if status in {"machine_draft", "draft", "reviewed"} and not include_machine_drafts:
            raise ValueError(f"Unapproved translation requires explicit inclusion: {row['record_id']}")
        if status not in {"machine_draft", "draft", "reviewed", "approved", "validated", "tested_in_game"}:
            raise ValueError(f"Translation status is not buildable: {row.get('status')}")
        targets.append((row, entry_id, subfile_id, message_id))

    known = {(member.entry_id, member.subfile_id): member for member in archive.members}
    for row, entry_id, subfile_id, message_id in targets:
        member_key = (entry_id, subfile_id)
        member = known.get(member_key)
        if member is None:
            raise ValueError(f"Translation member does not exist: {row['record_id']}")
        text_file = TextFile.parse(member.data)
        if message_id >= len(text_file.lines):
            raise ValueError(f"Translation message does not exist: {row['record_id']}")
        line = text_file.lines[message_id]
        if source_variant_hash(line.decoded_words) != row.get("source_variant_sha256"):
            raise ValueError(f"Source variant hash mismatch: {row['record_id']}")
        source_controls = [segment["control_words"] for segment in row["translation_segments"] if "control_words" in segment]
        # Translate source events back to the ordered raw-word signature.
        source_events: list[list[str]] = []
        index = 0
        words_source = line.decoded_words
        while index < len(words_source):
            value = words_source[index]
            if value == 0:
                break
            if value == 0x0010:
                count = words_source[index + 1]
                source_events.append([f"{word:04X}" for word in words_source[index:index + 2 + count]])
                index += 2 + count
            elif value == 0x000A:
                source_events.append(["000A"])
                index += 1
            else:
                index += 1
        if source_controls != source_events:
            raise ValueError(f"Control/placeholder sequence mismatch: {row['record_id']}")
        words = translation_words(row)
        member_replacements = replacement_by_member.setdefault(member_key, {})
        if message_id in member_replacements:
            raise ValueError(f"Duplicate translation target: {row['record_id']}")
        member_replacements[message_id] = words

    replacement_members: dict[tuple[int, int], bytes] = {}
    untouched_message_count = 0
    for member_key, replacements in replacement_by_member.items():
        original_member = known[member_key]
        original_tf = TextFile.parse(original_member.data)
        rebuilt_tf = original_tf.rebuild(replacements)
        rebuilt_parsed = TextFile.parse(rebuilt_tf)
        for message_id, line in enumerate(original_tf.lines):
            rebuilt_words = rebuilt_parsed.lines[message_id].decoded_words
            if message_id not in replacements:
                if rebuilt_words != line.decoded_words:
                    raise MessageError(f"Untouched message changed at member {member_key}, message {message_id}")
                untouched_message_count += 1
            elif rebuilt_words != replacements[message_id] + line.terminator_suffix:
                raise MessageError(f"Translated message differs from requested words at member {member_key}, message {message_id}")
        replacement_members[member_key] = rebuilt_tf

    output = archive.rebuild(replacement_members)
    rebuilt_archive = GARC.parse(output)
    if rebuilt_archive.rebuild() != output:
        raise GARCError(f"Rebuilt GARC no-change round trip is not byte-exact: {resource}")
    rebuilt_members = {(member.entry_id, member.subfile_id): member for member in rebuilt_archive.members}
    if set(rebuilt_members) != set(known):
        raise GARCError("GARC member coordinate set changed during rebuild")
    for key, original in known.items():
        if key not in replacement_members and rebuilt_members[key].data != original.data:
            raise GARCError(f"Unrelated GARC member changed during rebuild: {key}")
    proof = {
        "source_sha256": sha256(source_bytes),
        "output_sha256": sha256(output),
        "source_size": len(source_bytes),
        "output_size": len(output),
        "garc_members": len(known),
        "modified_members": len(replacement_members),
        "unrelated_members_verified_unchanged": len(known) - len(replacement_members),
        "untranslated_messages_verified_unchanged": untouched_message_count,
        "messages_applied": len(targets),
        "message_ids": [row["record_id"] for row, *_ in targets],
    }
    return output, proof
