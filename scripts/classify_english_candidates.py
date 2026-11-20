#!/usr/bin/env python3
"""Report high-confidence English-text candidates outside known English resources."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ENGLISH_FUNCTION_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do", "for", "from",
    "get", "got", "have", "he", "her", "here", "him", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "let", "me", "my", "no", "not", "of", "on", "or", "our", "out", "she",
    "so", "that", "the", "their", "them", "there", "they", "this", "to", "up", "was", "we",
    "were", "what", "when", "where", "which", "who", "will", "with", "you", "your",
}
LATIN_RE = re.compile(r"[A-Za-z]+")


def english_candidate(text: str) -> tuple[str, float, dict[str, int]]:
    """Return a conservative lexical candidate label; this is not language detection."""
    words = LATIN_RE.findall(text.lower())
    letters = [char for char in text if char.isalpha()]
    latin = sum("a" <= char.lower() <= "z" for char in letters)
    hits = [word for word in words if word in ENGLISH_FUNCTION_WORDS]
    distinct_hits = len(set(hits))
    ratio = len(hits) / max(1, len(words))
    stats = {"words": len(words), "english_function_word_hits": len(hits), "distinct_function_words": distinct_hits}
    if len(text) >= 40 and len(words) >= 8 and latin / max(1, len(letters)) >= 0.9 and len(hits) >= 8 and distinct_hits >= 5 and ratio >= 0.18:
        return "high_confidence_candidate", 0.90, stats
    if len(text) >= 24 and len(words) >= 5 and latin / max(1, len(letters)) >= 0.9 and len(hits) >= 5 and distinct_hits >= 4 and ratio >= 0.18:
        return "review_candidate", 0.70, stats
    return "undetermined", 0.0, stats


def classify_catalog(catalog_path: Path) -> dict:
    known = Counter()
    candidate_by_resource: dict[str, Counter] = {}
    samples: list[dict] = []
    with catalog_path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            language = row.get("source_language", "undetermined")
            if language == "en":
                known["known_english_path_variants"] += 1
                continue
            known["undetermined_variants"] += 1
            label, confidence, stats = english_candidate(str(row.get("source_text", "")))
            if label == "undetermined":
                continue
            resource = str(row.get("resource", "unknown"))
            counter = candidate_by_resource.setdefault(resource, Counter())
            counter[label] += 1
            if label == "high_confidence_candidate" and len(samples) < 50:
                samples.append({
                    "record_id": row["record_id"],
                    "source_variant_sha256": row["source_variant_sha256"],
                    "resource": resource,
                    "confidence": confidence,
                    "lexical_features": stats,
                })
    return {
        "schema_version": 1,
        "method": "conservative English function-word heuristic; candidates are not promoted to English without review",
        "known": dict(known),
        "candidates_by_resource": {key: dict(value) for key, value in sorted(candidate_by_resource.items())},
        "high_confidence_candidate_count": sum(v["high_confidence_candidate"] for v in candidate_by_resource.values()),
        "review_candidate_count": sum(v["review_candidate"] for v in candidate_by_resource.values()),
        "sample_ids_only": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/milestone-3e/language-candidates.json")
    args = parser.parse_args()
    result = classify_catalog(args.catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: result[key] for key in ("known", "high_confidence_candidate_count", "review_candidate_count")}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
