#!/usr/bin/env python3
"""Build ignored glyph-coverage and long-text test archives for X and Y."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.fonts import font_metrics  # noqa: E402
from src.extraction.garc import GARC  # noqa: E402
from src.extraction.messages import MessageError, TextFile  # noqa: E402
from src.validation.text_constraints import analyze_text, enforce_text_limits  # noqa: E402

TITLE_IDS = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCE = "a/0/7/4"
TARGET_MEMBER = (85, 0)
TARGET_MESSAGE_ID = 1

GLYPH_SPANS = (
    "ВЕРХ: АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
    "низ: абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "",
    "Знаки: .,!?:;…—–-«»„“‘’()[]{}№",
    "Цифры: 0123456789",
    "Символы: +−×÷=/%#@&*",
    "Latin: AaZz 09",
    "Кавычки: “Тест” ‘тест’",
    "Ёё ₽ ° © ® ™ •",
    "Микс: AaЯяЁё 09!?",
)

LONG_TEXT_SPANS = (
    "Проверка длинной строки: АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
    "Далее строчные буквы: абвгдеёжзийклмнопрстуфхцчшщъыьэюя и числа 0123456789.",
    "",
    "",
    "Эта строка намеренно значительно длиннее исходного поля и проверяет перенос текста через ширину панели.",
    "Продолжение: широкий текст, кавычки «проверка», длинное тире — и многоточие… плюс цифры 1234567890.",
    "",
    "",
    "Этот абзац проверяет, помещается ли весь текст по высоте и что происходит при переполнении окна.",
    "Конец теста.",
)

VARIANTS = {"glyph-coverage": GLYPH_SPANS, "long-text": LONG_TEXT_SPANS}
BUILD_ROOT = (ROOT / "build/milestone-3a").resolve()


def contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def split_visible_spans(line) -> tuple[list[str], list[tuple[int, ...]]]:
    """Find printable runs and retain each original control token as raw words."""
    words = line.decoded_words
    spans: list[str] = []
    controls: list[tuple[int, ...]] = []
    current: list[int] = []
    i = 0
    single_tokens = {0x000A, 0x005C, 0xE07F, 0xE08D, 0xE08E, 0xE08F}
    while i < len(words):
        word = words[i]
        if word == 0:
            break
        if word in single_tokens:
            spans.append("".join(chr(unit) for unit in current))
            current.clear()
            controls.append((word,))
            i += 1
        elif word == 0x0010:
            if i + 2 >= len(words):
                raise MessageError("Truncated TextFile control sequence in rendering test target")
            count = words[i + 1]
            if count < 1 or i + 1 + count >= len(words):
                raise MessageError("Invalid TextFile control length in rendering test target")
            spans.append("".join(chr(unit) for unit in current))
            current.clear()
            end = i + 2 + count
            controls.append(tuple(words[i:end]))
            i = end
        elif 0xE000 <= word <= 0xF8FF:
            spans.append("".join(chr(unit) for unit in current))
            current.clear()
            controls.append((word,))
            i += 1
        else:
            current.append(word)
            i += 1
    spans.append("".join(chr(unit) for unit in current))
    return spans, controls


def make_control_preserving_body(line, replacement_spans: tuple[str, ...]) -> tuple[int, ...]:
    _source_spans, controls = split_visible_spans(line)
    if len(replacement_spans) != len(controls) + 1:
        raise MessageError(f"Expected {len(controls) + 1} printable spans; received {len(replacement_spans)}")
    result: list[int] = []
    for index, control in enumerate(controls):
        for character in replacement_spans[index]:
            codepoint = ord(character)
            if codepoint > 0xFFFF or 0xD800 <= codepoint <= 0xDFFF:
                raise MessageError(f"Test string contains unsupported non-BMP character U+{codepoint:04X}")
        result.extend(map(ord, replacement_spans[index]))
        result.extend(control)
    result.extend(map(ord, replacement_spans[-1]))
    return tuple(result)


def build_font_report(test_spans: tuple[str, ...]) -> tuple[frozenset[int], list[dict[str, object]]]:
    archive_path = ROOT / "workspace/pokemon-x/base/a/1/8/5"
    archive = GARC.parse(archive_path.read_bytes())
    metrics_reports = []
    union: set[int] = set()
    for member in archive.members:
        metrics = font_metrics(member.data)
        union.update(metrics.mapped_codepoints)
        test_widths = []
        for span_index, span in enumerate(test_spans):
            advances = [metrics.advance(ord(character)) for character in span]
            unknown = sorted({ord(character) for character, advance in zip(span, advances) if advance is None})
            test_widths.append({
                "span_index": span_index,
                "codepoints": len(span),
                "known_advance_sum": sum(advance for advance in advances if advance is not None),
                "complete_cwdh_advance": sum(advances) if all(advance is not None for advance in advances) else None,
                "unmeasured_codepoints": [f"U+{cp:04X}" for cp in unknown],
            })
        english_reference = "Use the +Control Pad to select a language."
        english_advances = [metrics.advance(ord(character)) for character in english_reference]
        metrics_reports.append({
            "member": [member.entry_id, member.subfile_id],
            "mapped_codepoints": len(metrics.mapped_codepoints),
            "cyrillic_basic_mapped": sum(cp in metrics.mapped_codepoints for cp in range(0x0410, 0x0450)),
            "yo_upper_mapped": 0x0401 in metrics.mapped_codepoints,
            "yo_lower_mapped": 0x0451 in metrics.mapped_codepoints,
            "alternate_glyph_index": metrics.alternate_glyph_index,
            "alternate_glyph_advance": metrics.alternate_advance,
            "default_width": metrics.default_width,
            "english_reference_codepoints": len(english_reference),
            "english_reference_cwdh_advance": sum(english_advances) if all(v is not None for v in english_advances) else None,
            "test_span_cwdh_estimates": test_widths,
        })
    return frozenset(union), metrics_reports


def build_one(game: str, variant: str, spans: tuple[str, ...], font_coverage: frozenset[int], font_report: list[dict[str, object]]) -> dict[str, object]:
    source = ROOT / "workspace" / game / "update-1.5" / Path(*RESOURCE.split("/"))
    if not contained(source, ROOT / "workspace") or not source.is_file():
        raise FileNotFoundError(f"Expected update 1.5 source archive is missing: {source}")
    source_raw = source.read_bytes()
    archive = GARC.parse(source_raw)
    members = {(member.entry_id, member.subfile_id): member.data for member in archive.members}
    if TARGET_MEMBER not in members:
        raise MessageError(f"Target GARC member {TARGET_MEMBER} is absent in {game}")
    text = TextFile.parse(members[TARGET_MEMBER])
    if len(text.lines) <= TARGET_MESSAGE_ID:
        raise MessageError(f"Target language-screen message is absent in {game}")
    line = text.lines[TARGET_MESSAGE_ID]
    source_spans, source_controls = split_visible_spans(line)
    if len(source_spans) != len(spans) or len(source_controls) != len(line.tokens):
        raise MessageError(f"Unexpected language-screen control structure in {game}")
    replacement_body = make_control_preserving_body(line, spans)
    edited_text = text.rebuild({TARGET_MESSAGE_ID: replacement_body})
    edited_archive = archive.rebuild({TARGET_MEMBER: edited_text})
    rebuilt_archive = GARC.parse(edited_archive)
    rebuilt_members = {(member.entry_id, member.subfile_id): member.data for member in rebuilt_archive.members}
    if set(rebuilt_members) != set(members):
        raise MessageError("GARC member set changed during rendering-test rebuild")
    for key, original in members.items():
        if key != TARGET_MEMBER and rebuilt_members[key] != original:
            raise MessageError(f"Unrelated GARC member changed during rebuild: {game}/{key}")
    rebuilt_text = TextFile.parse(rebuilt_members[TARGET_MEMBER])
    rebuilt_line = rebuilt_text.lines[TARGET_MESSAGE_ID]
    if rebuilt_line.tokens != line.tokens:
        raise MessageError("Control codes or placeholders changed in rendering-test message")
    visible_text = "".join(spans)
    if not all(character in rebuilt_line.display_text for character in set(visible_text) if character != ""):
        raise MessageError("One or more requested test glyphs did not survive TextFile serialization")

    visible_text = "".join(spans)
    layout = analyze_text(visible_text, font_coverage)
    max_line = max(len(item) for item in spans)
    enforce_text_limits(visible_text, max_utf16_units=0xFFFF)
    output = BUILD_ROOT / variant / game / TITLE_IDS[game] / "romfs" / Path(*RESOURCE.split("/"))
    if not contained(output, BUILD_ROOT):
        raise RuntimeError(f"Refusing output outside build directory: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(edited_archive)
    return {
        "game": game,
        "variant": variant,
        "base_title_id": TITLE_IDS[game],
        "source_resource": RESOURCE,
        "source_version": "update-1.5",
        "target_member": list(TARGET_MEMBER),
        "target_message_id": TARGET_MESSAGE_ID,
        "preserved_control_tokens": len(line.tokens),
        "preserved_unmodified_members": len(members) - 1,
        "source_archive_sha256": hashlib.sha256(source_raw).hexdigest(),
        "output_archive_sha256": hashlib.sha256(edited_archive).hexdigest(),
        "output_archive_size": len(edited_archive),
        "test_spans": list(spans),
        "visible_text_utf16_units_excluding_controls": layout.utf16_units,
        "explicit_span_codepoint_lengths": [len(item) for item in spans],
        "max_span_codepoints": max_line,
        "unmapped_game_cfnt_codepoints": [f"U+{cp:04X}" for cp in layout.unsupported_codepoints],
        "font_members": font_report,
        "install_performed": False,
        "output": output.relative_to(ROOT).as_posix(),
    }


def main() -> int:
    font_report = []
    results = []
    for variant, spans in VARIANTS.items():
        coverage, font_report = build_font_report(spans)
        results.extend(build_one(game, variant, spans, coverage, font_report) for game in TITLE_IDS)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    (BUILD_ROOT / "render-validation-report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )
    summary = [{
        "game": row["game"], "variant": row["variant"], "target": row["output"],
        "sha256": row["output_archive_sha256"], "size": row["output_archive_size"],
        "preserved_controls": row["preserved_control_tokens"],
        "preserved_members": row["preserved_unmodified_members"],
        "max_span_codepoints": row["max_span_codepoints"],
        "unmapped_game_cfnt_codepoints": len(row["unmapped_game_cfnt_codepoints"]),
    } for row in results]
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
