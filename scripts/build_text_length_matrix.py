#!/usr/bin/env python3
"""Build reproducible, same-format text-length probes under ignored build/."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.garc import GARC  # noqa: E402
from src.extraction.messages import MessageError, TextFile  # noqa: E402
from scripts.build_render_validation import (  # noqa: E402
    BUILD_ROOT,
    GLYPH_SPANS,
    RESOURCE,
    TARGET_MEMBER,
    TARGET_MESSAGE_ID,
    TITLE_IDS,
    make_control_preserving_body,
    split_visible_spans,
)

MATRIX_ROOT = BUILD_ROOT / "length-matrix"
BASE_TOTAL = sum(map(len, GLYPH_SPANS))
FILLER = "я"
TOTAL_WORD_TARGETS = (295, 350, 400, 450, 480, 500, 512, 527)
SINGLE_SPAN_TARGETS = (43, 58, 75, 103)


def extend_total(spans: tuple[str, ...], target_chars: int) -> tuple[str, ...]:
    """Append Cyrillic filler evenly across nonempty spans, preserving controls."""
    if target_chars < sum(map(len, spans)):
        raise ValueError("Target character count cannot be below the glyph baseline")
    result = list(spans)
    eligible = [index for index, span in enumerate(result) if span]
    remaining = target_chars - sum(map(len, result))
    cursor = 0
    while remaining:
        result[eligible[cursor % len(eligible)]] += FILLER
        cursor += 1
        remaining -= 1
    return tuple(result)


def extend_first_span(spans: tuple[str, ...], target_length: int) -> tuple[str, ...]:
    """Vary one explicit line while holding every other text span constant."""
    if target_length < len(spans[0]):
        raise ValueError("Target line length cannot be below the glyph baseline")
    result = list(spans)
    result[0] += FILLER * (target_length - len(result[0]))
    return tuple(result)


def _read_source(game: str):
    source = ROOT / "workspace" / game / "update-1.5" / Path(*RESOURCE.split("/"))
    raw = source.read_bytes()
    archive = GARC.parse(raw)
    member = next((m for m in archive.members if (m.entry_id, m.subfile_id) == TARGET_MEMBER), None)
    if member is None:
        raise MessageError(f"Target member {TARGET_MEMBER} missing for {game}")
    text = TextFile.parse(member.data)
    line = text.lines[TARGET_MESSAGE_ID]
    source_spans, controls = split_visible_spans(line)
    if len(source_spans) != len(GLYPH_SPANS):
        raise MessageError(f"Source formatting span count changed for {game}")
    return source, raw, archive, member, text, line, controls


def _build_one(game: str, variant: str, spans: tuple[str, ...]) -> dict[str, object]:
    source, source_raw, archive, member, text, line, source_controls = _read_source(game)
    body = make_control_preserving_body(line, spans)
    rebuilt_text_raw = text.rebuild({TARGET_MESSAGE_ID: body})
    rebuilt_text = TextFile.parse(rebuilt_text_raw)
    rebuilt_line = rebuilt_text.lines[TARGET_MESSAGE_ID]
    output_spans, output_controls = split_visible_spans(rebuilt_line)
    if output_spans != list(spans):
        raise MessageError(f"Visible spans did not round-trip for {game}/{variant}")
    if output_controls != source_controls:
        raise MessageError(f"Raw control sequence changed for {game}/{variant}")
    for message_id, (before, after) in enumerate(zip(text.lines, rebuilt_text.lines)):
        if message_id == TARGET_MESSAGE_ID:
            continue
        if (before.decoded_words, before.encrypted_words, before.table_reserved, before.padding_after) != (
            after.decoded_words, after.encrypted_words, after.table_reserved, after.padding_after
        ):
            raise MessageError(f"Untargeted TextFile message changed: {game}/{variant}/{message_id}")

    rebuilt_archive_raw = archive.rebuild({TARGET_MEMBER: rebuilt_text_raw})
    reparsed_archive = GARC.parse(rebuilt_archive_raw)
    reparsed_members = {(m.entry_id, m.subfile_id): m.data for m in reparsed_archive.members}
    original_members = {(m.entry_id, m.subfile_id): m.data for m in archive.members}
    if set(reparsed_members) != set(original_members):
        raise MessageError(f"GARC member set changed for {game}/{variant}")
    if reparsed_members[TARGET_MEMBER] != rebuilt_text_raw:
        raise MessageError(f"Repacked target member mismatch for {game}/{variant}")
    changed = [key for key in original_members if reparsed_members[key] != original_members[key]]
    if changed != [TARGET_MEMBER]:
        raise MessageError(f"Unexpected changed archive members in {game}/{variant}: {changed}")

    output = MATRIX_ROOT / variant / game / TITLE_IDS[game] / "romfs" / Path(*RESOURCE.split("/"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(rebuilt_archive_raw)
    digest = hashlib.sha256(rebuilt_archive_raw).hexdigest()
    return {
        "game": game,
        "variant": variant,
        "target": output.relative_to(ROOT).as_posix(),
        "sha256": digest,
        "archive_size": len(rebuilt_archive_raw),
        "target_member": list(TARGET_MEMBER),
        "message_id": TARGET_MESSAGE_ID,
        "textfile_header_hex": rebuilt_text_raw[:16].hex(),
        "target_record_offset": rebuilt_line.relative_offset,
        "target_record_reserved": rebuilt_line.table_reserved,
        "target_record_words": len(rebuilt_line.decoded_words),
        "target_record_bytes": len(rebuilt_line.decoded_words) * 2,
        "visible_character_count": sum(map(len, spans)),
        "explicit_span_lengths": [len(span) for span in spans],
        "control_words": [list(control) for control in source_controls],
        "control_word_count": sum(map(len, source_controls)),
        "preserved_non_target_members": len(original_members) - 1,
        "source_archive_sha256": hashlib.sha256(source_raw).hexdigest(),
        "install_performed": False,
        "source": source.relative_to(ROOT).as_posix(),
    }


def build_matrix() -> list[dict[str, object]]:
    baseline_total = BASE_TOTAL
    variants: list[tuple[str, tuple[str, ...]]] = []
    for target_words in TOTAL_WORD_TARGETS:
        # This calculation also accounts for the source record's fixed control
        # stream and preserved suffix; validate exact record size after rebuild.
        spans = extend_total(GLYPH_SPANS, baseline_total + target_words - 295)
        variants.append((f"record-{target_words}-words", spans))
    for target_length in SINGLE_SPAN_TARGETS:
        variants.append((f"line-0-{target_length}-chars", extend_first_span(GLYPH_SPANS, target_length)))

    rows = [_build_one(game, variant, spans) for variant, spans in variants for game in TITLE_IDS]
    for target_words in TOTAL_WORD_TARGETS:
        for game in TITLE_IDS:
            row = next(r for r in rows if r["game"] == game and r["variant"] == f"record-{target_words}-words")
            if row["target_record_words"] != target_words:
                raise MessageError(
                    f"Expected {target_words} target record words, got {row['target_record_words']} "
                    f"for {game}; check terminator/suffix accounting"
                )
    report = MATRIX_ROOT / "matrix-report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows


def main() -> int:
    rows = build_matrix()
    print(json.dumps([
        {"game": r["game"], "variant": r["variant"], "words": r["target_record_words"],
         "visible_chars": r["visible_character_count"], "max_span": max(r["explicit_span_lengths"]),
         "sha256": r["sha256"]}
        for r in rows
    ], ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
