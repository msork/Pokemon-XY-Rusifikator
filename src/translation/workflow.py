"""Deterministic export/import helpers for human-reviewed translation batches."""

from __future__ import annotations

from typing import Any

from src.translation.catalog import validate_translation_rows


def translation_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("record_id", "")), str(row.get("source_variant_sha256", ""))


def export_batch(source_rows: list[dict[str, Any]], record_ids: set[str]) -> list[dict[str, Any]]:
    """Create editable drafts; retain controls in place and expose source context locally."""
    selected = [row for row in source_rows if row["record_id"] in record_ids]
    found = {row["record_id"] for row in selected}
    missing = record_ids - found
    if missing:
        raise ValueError("Unknown source record IDs: " + ", ".join(sorted(missing)))
    result = []
    for source in selected:
        segments = []
        for segment in source["source_segments"]:
            if "text" in segment:
                segments.append({"text": ""})
            else:
                segments.append({"control_words": list(segment["control_words"])})
        occurrences = source.get("occurrences", [])
        datasets = sorted({str(item["dataset"]) for item in occurrences})
        games = {dataset.split("/")[0] for dataset in datasets}
        versions = sorted({dataset.split("/")[-1] for dataset in datasets})
        scope = "shared" if games == {"pokemon-x", "pokemon-y"} else ("x" if "pokemon-x" in games else "y")
        result.append({
            "record_id": source["record_id"],
            "source_variant_sha256": source["source_variant_sha256"],
            "source_text": source["source_text"],
            "source_segments": source["source_segments"],
            "context": source.get("context"),
            "occurrences": datasets,
            "scope": scope,
            "version_scope": versions,
            "translation_segments": segments,
            "status": "draft",
        })
    return sorted(result, key=translation_key)


def import_batch(source_rows: list[dict[str, Any]], batch_rows: list[dict[str, Any]],
                 existing_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate editable batch provenance/tokens and merge without touching other records."""
    source_by_key = {(row["record_id"], row["source_variant_sha256"]): row for row in source_rows}
    errors = []
    clean = []
    for row in batch_rows:
        key = translation_key(row)
        source = source_by_key.get(key)
        if source is None:
            errors.append(f"unknown or stale source record: {key[0]}")
            continue
        if row.get("source_text") != source["source_text"] or row.get("source_segments") != source["source_segments"]:
            errors.append(f"source text or segments changed in translation batch: {key[0]}")
        actual_datasets = sorted({str(item["dataset"]) for item in source.get("occurrences", [])})
        if row.get("occurrences") != actual_datasets:
            errors.append(f"source provenance changed in translation batch: {key[0]}")
        candidate = {name: value for name, value in row.items()
                     if name not in {"source_text", "source_segments", "occurrences"}}
        clean.append(candidate)
    errors.extend(validate_translation_rows(
        [source_by_key[translation_key(row)] for row in clean if translation_key(row) in source_by_key], clean))
    if errors:
        raise ValueError("\n".join(errors))
    merged = {translation_key(row): row for row in existing_rows}
    for row in clean:
        merged[translation_key(row)] = row
    return sorted(merged.values(), key=translation_key)
