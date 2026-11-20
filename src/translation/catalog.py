"""Deterministic, read-only catalog helpers for Gen VI TextFile messages."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from src.extraction.garc import GARC
from src.extraction.lz11 import decompress
from src.extraction.messages import TextFile, MessageError


ROMFS_ROOT = Path(__file__).resolve().parents[2] / "workspace"
GARC_MAGIC = b"CRAG"
MAX_LZ11_OUTPUT = 64 * 1024 * 1024
MAX_GARC_SCAN = 128 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _textfile_blob(blob: bytes) -> bytes:
    return decompress(blob, max_output=MAX_LZ11_OUTPUT) if blob.startswith(b"\x11") else blob


def _segments(words: tuple[int, ...]) -> list[dict[str, Any]]:
    """Split text from exact control words, retaining all variable arguments."""
    end = len(words)
    i = 0
    while i < len(words):
        value = words[i]
        if value == 0:
            end = i
            break
        if value == 0x0010:
            if i + 2 >= len(words):
                raise ValueError("truncated length-prefixed control event")
            count = words[i + 1]
            if count < 1 or i + 2 + count > len(words):
                raise ValueError("invalid length-prefixed control event")
            i += 2 + count
        else:
            i += 1
    body = words[:end]
    result: list[dict[str, Any]] = []
    text: list[int] = []
    i = 0
    while i < len(body):
        value = body[i]
        if value == 0x0010:
            count = body[i + 1]
            if count < 1 or i + 2 + count > len(body):
                raise ValueError("malformed length-prefixed control event")
            if text:
                result.append({"text": "".join(chr(w) for w in text)})
                text.clear()
            event = body[i:i + 2 + count]
            result.append({"control_words": [f"{word:04X}" for word in event]})
            i += len(event)
        elif value == 0x000A:
            if text:
                result.append({"text": "".join(chr(w) for w in text)})
                text.clear()
            result.append({"control_words": ["000A"]})
            i += 1
        else:
            text.append(value)
            i += 1
    if text:
        result.append({"text": "".join(chr(w) for w in text)})
    return result


def _message_hash(words: tuple[int, ...]) -> str:
    return sha256(b"".join(word.to_bytes(2, "little") for word in words))


def duplicate_source_text_stats(records: list[dict[str, Any]]) -> tuple[int, int]:
    """Count identical display text at distinct records without merging their IDs."""
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        counts[sha256(str(record["source_text"]).encode("utf-8"))] += 1
    duplicates = [count for count in counts.values() if count > 1]
    return len(duplicates), sum(duplicates)


def catalog_roots(roots: list[Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read all files in supplied RomFS roots; return TextFile records and scan report."""
    grouped: dict[tuple[str, int, int, int, str], dict[str, Any]] = {}
    report: dict[str, Any] = {"files_scanned": 0, "garc_candidates": 0, "garc_parsed": 0,
                              "textfile_members": 0, "messages": 0, "non_text_members": 0,
                              "garc_errors": [], "member_errors": []}
    for root in sorted((path.resolve(strict=True) for path in roots), key=lambda p: p.as_posix()):
        root_label = root.relative_to(ROMFS_ROOT.resolve()).as_posix()
        for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
            report["files_scanned"] += 1
            try:
                size = path.stat().st_size
                with path.open("rb") as stream:
                    magic = stream.read(4)
            except OSError as exc:
                report["garc_errors"].append({"path": path.as_posix(), "error": str(exc)})
                continue
            if magic != GARC_MAGIC:
                continue
            report["garc_candidates"] += 1
            rel = path.relative_to(root).as_posix()
            if size > MAX_GARC_SCAN:
                report.setdefault("oversized_garc_skipped", []).append({"path": f"{root_label}/{rel}", "size": size, "limit": MAX_GARC_SCAN})
                continue
            try:
                raw = path.read_bytes()
                archive = GARC.parse(raw)
            except ValueError as exc:
                report["garc_errors"].append({"path": f"{root_label}/{rel}", "error": str(exc)})
                continue
            report["garc_parsed"] += 1
            archive_hash = sha256(raw)
            for member in archive.members:
                try:
                    member_data = _textfile_blob(member.data)
                    textfile = TextFile.parse(member_data)
                except (ValueError, MessageError) as exc:
                    report["non_text_members"] += 1
                    if member.data.startswith(b"\x11"):
                        # A non-TextFile LZ11 payload is expected for many archives.
                        pass
                    elif member.data[:4] in (b"CFNT", b"CFNU"):
                        pass
                    elif member.data[:4] not in (b"CRAG",):
                        report["member_errors"].append({
                            "path": f"{root_label}/{rel}", "member": f"{member.entry_id}/{member.subfile_id}",
                            "error": str(exc), "magic": member.data[:4].hex(),
                        })
                    continue
                report["textfile_members"] += 1
                member_hash = sha256(member.data)
                textfile_hash = sha256(member_data)
                for line in textfile.lines:
                    words = line.decoded_words
                    try:
                        segments = _segments(words)
                    except ValueError as exc:
                        raise ValueError(f"{root_label}/{rel} member {member.entry_id}/{member.subfile_id} message {line.message_id}: {exc}; context={words[max(0, words.index(0x0010) - 2):][:12] if 0x0010 in words else words[:12]}") from exc
                    plain = "".join(str(segment.get("text", "")) for segment in segments)
                    identity = (rel, member.entry_id, member.subfile_id, line.message_id, _message_hash(words))
                    record = grouped.setdefault(identity, {
                        "record_id": f"gen6:{rel}:{member.entry_id:04d}/{member.subfile_id:02d}:{line.message_id:05d}",
                        "source_language": "en" if rel in {"a/0/7/4", "a/0/8/2"} else "undetermined",
                        "context": None,
                        "resource": rel, "member_id": [member.entry_id, member.subfile_id],
                        "message_id": line.message_id, "source_variant_sha256": _message_hash(words),
                        "source_word_count": len(words), "relative_message_offset": line.relative_offset,
                        "table_reserved": line.table_reserved,
                        "padding_after_hex": line.padding_after.hex(),
                        "terminator_suffix_words": [f"{word:04X}" for word in line.terminator_suffix],
                        "source_text": plain,
                        "source_segments": segments,
                        "control_events": [segment["control_words"] for segment in segments if "control_words" in segment],
                        "occurrences": [],
                    })
                    record["occurrences"].append({
                        "dataset": root_label, "archive_path": rel, "archive_sha256": archive_hash,
                        "member_sha256": member_hash, "textfile_sha256": textfile_hash,
                        "compressed_lz11": member.data.startswith(b"\x11"),
                    })
                    report["messages"] += 1
    records = list(grouped.values())
    for record in records:
        record["occurrences"].sort(key=lambda item: item["dataset"])
    records.sort(key=lambda item: (item["resource"], item["member_id"], item["message_id"], item["source_variant_sha256"]))
    report["unique_coordinate_variants"] = len(records)
    report["duplicate_source_text_groups"], report["duplicate_source_text_records"] = duplicate_source_text_stats(records)
    report["roots"] = [p.as_posix() for p in roots]
    return records, report


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSON: {exc}") from exc
    return rows


def validate_species_document(document: dict[str, Any]) -> None:
    entries = document.get("entries")
    if not isinstance(entries, list) or len(entries) != 721:
        raise ValueError("Expected exactly 721 species entries")
    numbers = [entry.get("national_dex_number") for entry in entries]
    if numbers != list(range(1, 722)):
        raise ValueError("National Dex identifiers must be unique and contiguous from 1 through 721")
    english = [entry.get("english", "").casefold() for entry in entries]
    if any(not name for name in english) or len(set(english)) != 721:
        raise ValueError("English species lookup keys must be nonempty and unique")
    russian = [entry.get("russian", "").casefold() for entry in entries]
    if any(not name for name in russian) or len(set(russian)) != 721:
        raise ValueError("Russian species names must be nonempty and unique in this source dataset")
    for entry in entries:
        for key in ("english", "russian"):
            value = entry.get(key)
            if not isinstance(value, str) or not value or unicodedata.normalize("NFC", value) != value:
                raise ValueError(f"Missing or non-NFC {key} at #{entry.get('national_dex_number')}")
        if entry.get("name_status") != "established_official_per_source":
            raise ValueError(f"Unexpected name status at #{entry['national_dex_number']}")


def species_lookup(document: dict[str, Any], english_name: str) -> dict[str, Any] | None:
    """Resolve an English species name case-insensitively through the validated dataset."""
    key = unicodedata.normalize("NFC", english_name).casefold()
    for entry in document.get("entries", []):
        if entry.get("english", "").casefold() == key:
            return entry
    return None


def validate_terms_glossary(document: dict[str, Any]) -> None:
    required = {"ui", "locations", "moves", "abilities", "items", "character_names", "battle_terminology", "system_messages"}
    categories = document.get("categories")
    if not isinstance(categories, dict) or not required.issubset(categories):
        raise ValueError("Terminology glossary is missing required categories")
    valid_statuses = set(document.get("status_values", []))
    for category, terms in categories.items():
        seen: set[str] = set()
        for term in terms:
            source = term.get("source")
            russian = term.get("russian")
            status = term.get("status")
            if not isinstance(source, str) or not source or source.casefold() in seen:
                raise ValueError(f"Missing or duplicate source term in {category}")
            seen.add(source.casefold())
            if status not in valid_statuses:
                raise ValueError(f"Unknown status for {category} term {source}")
            if status == "needs_research" and russian is not None:
                raise ValueError(f"Unresearched {category} term {source} must not have an invented translation")
            if russian is not None and (not isinstance(russian, str) or unicodedata.normalize("NFC", russian) != russian):
                raise ValueError(f"Invalid or non-NFC translation for {category} term {source}")


def species_name_consistency_errors(source_text: str, translation_segments: list[dict[str, Any]], species_document: dict[str, Any]) -> list[str]:
    """Flag source species names whose canonical Russian spelling is absent in the draft."""
    translated = "".join(segment.get("text", "") for segment in translation_segments if isinstance(segment, dict))
    errors = []
    entries = sorted(species_document.get("entries", []), key=lambda entry: len(entry.get("english", "")), reverse=True)
    for entry in entries:
        english = entry["english"]
        pattern = rf"(?<![\w]){re.escape(english)}(?![\w])"
        if re.search(pattern, source_text, flags=re.IGNORECASE) and entry["russian"].casefold() not in translated.casefold():
            errors.append(f"species name requires glossary spelling: {english} -> {entry['russian']}")
    return errors


def validate_translation_rows(source: list[dict[str, Any]], translations: list[dict[str, Any]],
                             species_document: dict[str, Any] | None = None,
                             terms_document: dict[str, Any] | None = None) -> list[str]:
    """Validate translation identifiers, segment shape, and exact protected-event order."""
    source_by_variant = {(row["record_id"], row["source_variant_sha256"]): row for row in source}
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []
    for row in translations:
        rid = row.get("record_id")
        variant = row.get("source_variant_sha256")
        key = (rid, variant)
        if key in seen:
            errors.append(f"duplicate translation record_id/source variant: {rid}")
            continue
        seen.add(key)
        origin = source_by_variant.get(key)
        if origin is None:
            errors.append(f"unknown record_id/source variant: {rid}")
            continue
        if row.get("status") not in {"untranslated", "machine_draft", "draft", "reviewed", "approved", "validated", "tested_in_game"}:
            errors.append(f"invalid status: {rid}")
        if row.get("status") in {"reviewed", "approved", "validated", "tested_in_game"} and not row.get("reviewer"):
            errors.append(f"reviewer attribution is required for status {row.get('status')}: {rid}")
        if row.get("status") in {"approved", "validated", "tested_in_game"} and not row.get("approver"):
            errors.append(f"approver attribution is required for status {row.get('status')}: {rid}")
        if row.get("status") == "tested_in_game" and not row.get("runtime_evidence"):
            errors.append(f"runtime evidence is required for tested_in_game: {rid}")
        source_occurrences = origin.get("occurrences", [])
        if source_occurrences:
            expected_versions = sorted({str(item["dataset"]).split("/")[-1] for item in source_occurrences})
            expected_games = {str(item["dataset"]).split("/")[0] for item in source_occurrences}
            expected_scope = "shared" if expected_games == {"pokemon-x", "pokemon-y"} else ("x" if "pokemon-x" in expected_games else "y")
            if row.get("version_scope") != expected_versions:
                errors.append(f"version scope does not match source provenance: {rid}")
            if row.get("scope") != expected_scope:
                errors.append(f"game scope does not match source provenance: {rid}")
        segments = row.get("translation_segments")
        if not isinstance(segments, list):
            errors.append(f"missing translation_segments: {rid}")
            continue
        translated_controls = [seg.get("control_words") for seg in segments if isinstance(seg, dict) and "control_words" in seg]
        if translated_controls != origin["control_events"]:
            errors.append(f"control/placeholder sequence mismatch: {rid}")
        for seg in segments:
            if not isinstance(seg, dict) or set(seg) not in ({"text"}, {"control_words"}):
                errors.append(f"invalid segment structure: {rid}")
                continue
            if "text" in seg:
                value = seg["text"]
                if not isinstance(value, str) or unicodedata.normalize("NFC", value) != value:
                    errors.append(f"non-string or non-NFC translation text: {rid}")
                elif any(ord(ch) > 0xFFFF or 0xD800 <= ord(ch) <= 0xDFFF or (ord(ch) < 0x20 and ch != "\n") for ch in value):
                    errors.append(f"unsupported character in translation: {rid}")
        if len("".join(seg.get("text", "") for seg in segments if isinstance(seg, dict))) > max(1, len(origin["source_text"])) * 2.5:
            errors.append(f"suspicious text expansion: {rid}")
        if species_document is not None:
            errors.extend(f"{rid}: {error}" for error in species_name_consistency_errors(
                origin["source_text"], segments, species_document))
        if terms_document is not None:
            errors.extend(f"{rid}: {error}" for error in terminology_consistency_errors(
                origin["source_text"], segments, terms_document))
    return errors


def terminology_consistency_errors(source_text: str, translation_segments: list[dict[str, Any]],
                                   terms_document: dict[str, Any]) -> list[str]:
    """Check only explicitly enforced, exact-form glossary terms; inflections remain review work."""
    translated = "".join(segment.get("text", "") for segment in translation_segments if isinstance(segment, dict))
    errors = []
    for category, terms in terms_document.get("categories", {}).items():
        for term in terms:
            if not term.get("enforce") or not term.get("russian"):
                continue
            source = str(term["source"])
            russian = str(term["russian"])
            if re.search(rf"(?<![\w]){re.escape(source)}(?![\w])", source_text, flags=re.IGNORECASE) \
                    and russian.casefold() not in translated.casefold():
                errors.append(f"glossary term mismatch ({category}): {source} -> {russian}")
    return errors


def missing_translation_variants(source: list[dict[str, Any]], translations: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Return every catalog ID/source variant without a translation row."""
    present = {(row.get("record_id"), row.get("source_variant_sha256")) for row in translations}
    return sorted({(row["record_id"], row["source_variant_sha256"]) for row in source} - present)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
