#!/usr/bin/env python3
"""Generate a bounded, source-linked runtime checklist for milestone 3E drafts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GROUPS = [
    ("Language screen and Options", lambda rid: ":0075/" in rid),
    ("Character creation", lambda rid: False),
    ("Vaniville Town and opening home dialogue", lambda rid: ":0055/" in rid or ":0057/" in rid or ":0072/" in rid),
    ("Protagonist-specific branches", lambda rid: ":0053/" in rid),
    ("Aquacorde Town opening sequence", lambda rid: ":0049/" in rid),
    ("Starter selection interface", lambda rid: ":0063/" in rid),
    ("First-battle messages", lambda rid: any(f":{member:04d}/" in rid for member in (124, 125, 126))),
]


def display(segments: list[dict]) -> str:
    parts = []
    for segment in segments:
        if "text" in segment:
            parts.append(segment["text"].replace("|", "\\|"))
            continue
        words = segment["control_words"]
        if words == ["000A"]:
            label = "LINE BREAK"
        elif words == ["0010", "0001", "BE01"]:
            label = "PAGE BREAK"
        elif words[:2] == ["0010", "0002"]:
            label = "VARIABLE / PLACEHOLDER CONTROL"
        else:
            label = "CONTROL"
        parts.append(f"[{label}: {' '.join(words)}]")
    return "".join(parts)


def generate(catalog_path: Path, translation_paths: list[Path]) -> str:
    translations = {}
    for path in translation_paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                key = (row["record_id"], row["source_variant_sha256"])
                if key in translations:
                    raise ValueError(f"Duplicate record in checklist inputs: {key[0]}")
                translations[key] = row
    source_rows = {}
    with catalog_path.open(encoding="utf-8") as stream:
        for line in stream:
            source = json.loads(line)
            key = (source["record_id"], source["source_variant_sha256"])
            if key in translations:
                source_rows[key] = source
    if set(source_rows) != set(translations):
        raise ValueError("Checklist translation rows do not all match source catalog variants")

    lines = [
        "# Milestone 3E Early-Game Runtime Checklist",
        "",
        "All entries are draft text, prepared for controlled owner testing only. No new AzaharPlus runtime result is claimed. English and Russian are rendered segment-by-segment; control events are annotations that retain their original hexadecimal words. Source hashes identify the exact catalog variants used for the candidate build.",
        "",
        "## Test procedure",
        "",
        "Use disposable saves or begin a new game separately in Pokémon X and Pokémon Y with update 1.5 enabled. Do not overwrite an existing save. Check each visible line in the listed scene and report clipping, line breaks, substitutions, missing text, or incorrect branch selection. These candidates have not been installed.",
        "",
        "### Coverage caveats",
        "",
        "- The opening character-creation flow is not yet mapped to a text record. Do not treat the Pokédex Male/Female filter labels as protagonist selection.",
        "- Exact event triggers for most newly translated messages are inferred from the message contents and archive organization. They need runtime confirmation.",
        "- Protagonist correlation for branch records 2/3 is inferred from the named rival; verify it in each game and with both protagonist choices.",
        "- Some extracted English source segments contain U+FFFD replacement characters. Those source decode issues are preserved as displayed and need investigation before final review.",
        "- Owner-confirmed Milestone 3C runtime testing covered the earlier 12-record pilot in Pokémon X with a female protagonist (Options, mother, Calem, Shauna). Pokémon Y and Serena remain untested; that does not verify these new drafts.",
        "",
    ]

    assigned = set()
    for title, predicate in GROUPS:
        group = []
        for key, row in translations.items():
            rid = row["record_id"]
            if key not in assigned and predicate(rid):
                group.append((key, row))
        group.sort(key=lambda pair: pair[1]["record_id"])
        assigned.update(key for key, _ in group)
        lines += [f"## {title}", ""]
        if title == "Character creation":
            lines += ["No confirmed protagonist name/appearance prompt has been identified in the current English TextFile catalog. This is an unresolved scene/resource gap, not a zero-message translation claim.", ""]
            continue
        if not group:
            lines += ["No records in this group.", ""]
            continue
        if title == "Language screen and Options":
            lines += ["Verified scene note: the prior owner-tested 3C records were visible in the opening language-selection/Options flow in Pokémon X with a female protagonist. This milestone adds no runtime evidence.", ""]
        elif title == "Vaniville Town and opening home dialogue":
            lines += ["Scene location is inferred from the dialogue and resource context; only the earlier 3C pilot lines are owner-confirmed in X.", ""]
        elif title == "Aquacorde Town opening sequence":
            lines += ["Message IDs 0–59 in this member form the extracted Aquacorde opening dialogue set. Individual trigger order and conditional selection are not runtime-verified.", ""]
        elif title == "First-battle messages":
            lines += ["The records are battle templates keyed by message ID. Which templates occur during each starter matchup is conditional and must be checked in-game.", ""]
        for key, row in group:
            source = source_rows[key]
            source_segments = source["source_segments"]
            translated_segments = row["translation_segments"]
            if len(source_segments) != len(translated_segments):
                raise ValueError(f"Segment count mismatch for {row['record_id']}")
            resource, archive_member, message = row["record_id"].split(":")[1:]
            member_id = archive_member.split("/")[0]
            version_scope = ", ".join(row.get("version_scope", []))
            lines += [
                f"### `{resource}` · member `{member_id}/0` · message `{int(message):d}`",
                "",
                f"- Source SHA-256: `{row['source_variant_sha256']}`",
                f"- Source versions: {version_scope}",
                f"- Context: {row.get('context', 'unspecified')} (trigger not runtime-verified unless stated above)",
                f"- State: `{row.get('status')}`; human approval: pending",
                f"- English: {display(source_segments)}",
                f"- Russian draft: {display(translated_segments)}",
                "",
            ]
    if len(assigned) != len(translations):
        extra = sorted(row["record_id"] for key, row in translations.items() if key not in assigned)
        raise ValueError("Unassigned checklist rows: " + ", ".join(extra))
    lines += ["## Runtime result recording", "", "Record each game and protagonist choice separately. Mark only observed rendering results; do not promote draft/review status based on structural tests.", ""]
    lines += ["| Game | Protagonist | Scene/message IDs | Text visible | Layout/control result |", "|---|---|---|---|---|", "| Pokémon X | Male |  |  |  |", "| Pokémon X | Female |  |  |  |", "| Pokémon Y | Male |  |  |  |", "| Pokémon Y | Female |  |  |  |", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--translations", action="append", type=Path, default=[ROOT / "translations/pilot.jsonl"])
    parser.add_argument("--output", type=Path, default=ROOT / "docs/testing/milestone-3e-runtime-checklist.md")
    args = parser.parse_args()
    text = generate(args.catalog, args.translations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"checklist": args.output.as_posix(), "records": text.count("- Source SHA-256:")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
