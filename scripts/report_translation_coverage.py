#!/usr/bin/env python3
"""Create a deterministic corpus/translation coverage dashboard from local scan outputs."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_dashboard(catalog_path: Path, translation_paths: list[Path], scan_report_path: Path) -> dict:
    translations = {}
    for path in translation_paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                key = (row["record_id"], row["source_variant_sha256"])
                if key in translations:
                    raise ValueError(f"Duplicate translation key across files: {key[0]}")
                translations[key] = row

    variants_by_language: Counter[str] = Counter()
    variants_by_resource: Counter[str] = Counter()
    valid_translation_keys = set()
    english_keys = set()
    stale_keys = []
    statuses: Counter[str] = Counter()
    review_states: Counter[str] = Counter()
    total_variants = occurrences = 0
    with catalog_path.open(encoding="utf-8") as stream:
        for line in stream:
            source = json.loads(line)
            total_variants += 1
            occurrences += len(source.get("occurrences", []))
            language = str(source.get("source_language", "undetermined"))
            resource = str(source.get("resource", "unknown"))
            variants_by_language[language] += 1
            variants_by_resource[resource] += 1
            key = (source["record_id"], source["source_variant_sha256"])
            if language == "en":
                english_keys.add(key)
            if key in translations:
                valid_translation_keys.add(key)
    for key, row in translations.items():
        status = str(row.get("status", "invalid"))
        if key in valid_translation_keys:
            statuses[status] += 1
            review_states[str(row.get("review_state", "unreviewed"))] += 1
        else:
            stale_keys.append(key[0])
    if stale_keys:
        raise ValueError("Translation rows do not match catalog source hashes: " + ", ".join(sorted(stale_keys)))

    report = json.loads(scan_report_path.read_text(encoding="utf-8"))
    untranslated = total_variants - len(valid_translation_keys)
    identified_english = variants_by_language.get("en", 0)
    translated_english = len(valid_translation_keys & english_keys)
    unsupported = {
        "member_parse_rejections": report.get("non_text_members", 0),
        "oversized_archives_skipped": len(report.get("oversized_garc_skipped", [])),
        "oversized_archive_records": report.get("oversized_garc_skipped", []),
    }
    return {
        "schema_version": 1,
        "corpus": {
            "source_catalog_variants": total_variants,
            "source_occurrences_across_games_and_versions": occurrences,
            "variants_by_source_language_label": dict(sorted(variants_by_language.items())),
            "variants_by_resource": dict(sorted(variants_by_resource.items())),
            "textfile_members": report.get("textfile_members", 0),
            "parsed_messages_across_datasets": report.get("messages", 0),
        },
        "coverage": {
            "translated_records": len(valid_translation_keys),
            "draft": statuses.get("draft", 0) + statuses.get("machine_draft", 0),
            "reviewed": statuses.get("reviewed", 0),
            "approved": statuses.get("approved", 0),
            "validated": statuses.get("validated", 0),
            "tested_in_game": statuses.get("tested_in_game", 0),
            "assistant_reviewed_pending_human": review_states.get("assistant_reviewed_pending_human", 0),
            "untranslated_source_variants": untranslated,
            "coverage_percent": round(100 * len(valid_translation_keys) / total_variants, 6) if total_variants else 0,
            "identified_english_variants": identified_english,
            "translated_identified_english_variants": translated_english,
            "untranslated_identified_english_variants": max(0, identified_english - translated_english),
            "identified_english_coverage_percent": round(100 * translated_english / identified_english, 6) if identified_english else 0,
        },
        "unsupported_or_unclassified": unsupported,
        "scan": {
            "files_scanned": report.get("files_scanned", 0),
            "garc_candidates": report.get("garc_candidates", 0),
            "garc_parsed": report.get("garc_parsed", 0),
            "member_parse_rejections": report.get("non_text_members", 0),
            "duplicate_source_text_groups": report.get("duplicate_source_text_groups", 0),
            "duplicate_source_text_records": report.get("duplicate_source_text_records", 0),
        },
    }


def markdown(dashboard: dict) -> str:
    corpus = dashboard["corpus"]
    coverage = dashboard["coverage"]
    unsupported = dashboard["unsupported_or_unclassified"]
    lines = [
        "# Translation Coverage Dashboard",
        "",
        "Generated from the local ignored source catalog and scan report. This report counts unique coordinate/source-word variants; it does not imply all game text has been discovered.",
        "",
        "## Translation status",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Translated records | {coverage['translated_records']} |",
        f"| Draft / machine draft | {coverage['draft']} |",
        f"| Reviewed | {coverage['reviewed']} |",
        f"| Approved | {coverage['approved']} |",
        f"| Structurally validated | {coverage['validated']} |",
        f"| Tested in game | {coverage['tested_in_game']} |",
        f"| Assistant review recorded; human approval pending | {coverage['assistant_reviewed_pending_human']} |",
        f"| Untranslated source variants | {coverage['untranslated_source_variants']} |",
        f"| Coverage | {coverage['coverage_percent']:.6f}% |",
        f"| Identified English variants covered | {coverage['translated_identified_english_variants']:,} / {coverage['identified_english_variants']:,} ({coverage['identified_english_coverage_percent']:.6f}%) |",
        "",
        "Status counts are mutually exclusive. Assistant review evidence is tracked separately and never changes a draft into human-reviewed or approved content. Runtime notes supplied by the owner are not changed into translation approval states.",
        "",
        "## Parsed corpus",
        "",
        f"- {corpus['source_catalog_variants']:,} unique coordinate/source-word variants.",
        f"- {corpus['source_occurrences_across_games_and_versions']:,} occurrences across X/Y base and update datasets.",
        f"- {corpus['parsed_messages_across_datasets']:,} parsed message occurrences in {corpus['textfile_members']:,} TextFile members.",
        "- English-labeled resources are determined by the current catalog's resource-path classification (`a/0/7/4`, `a/0/8/2`); other parsed resources remain `undetermined`, not assumed English.",
        "",
        "| Catalog source-language label | Variants |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {value:,} |" for key, value in corpus["variants_by_source_language_label"].items())
    lines += ["", "| Resource | Variants |", "|---|---:|"]
    lines.extend(f"| `{key}` | {value:,} |" for key, value in corpus["variants_by_resource"].items())
    lines += [
        "",
        "## Unsupported and unclassified content",
        "",
        f"- {unsupported['member_parse_rejections']:,} GARC member payloads were not accepted as TextFiles by the current parser. This includes non-text formats and unsupported structures; it is not proof that every rejection contains translatable text.",
        f"- {unsupported['oversized_archives_skipped']} archive(s) exceeded the catalog parser's size cap; their text coverage is unverified.",
        "- Executable literals, non-GARC strings, images, fonts, graphics, audio, video, and text in formats not parsed as Gen VI TextFiles are outside this translation count.",
        "",
        "This dashboard measures the currently indexed catalog only. Full localization coverage cannot be claimed until unsupported formats and skipped archives are inspected.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--scan-report", type=Path, default=ROOT / "reports/milestone-3b/asset-catalog.json")
    parser.add_argument("--translations", action="append", type=Path,
                        default=[ROOT / "translations/pilot.jsonl"], help="may be repeated")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/milestone-3d")
    args = parser.parse_args()
    result = build_dashboard(args.catalog, args.translations, args.scan_report)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "coverage.json").write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    (args.output_dir / "coverage.md").write_text(markdown(result), encoding="utf-8", newline="\n")
    print(json.dumps(result["coverage"], ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
