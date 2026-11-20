#!/usr/bin/env python3
"""Apply the two narrowly scoped dialogue corrections documented for Milestone 3G."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "translations/early-game.jsonl"
GENDER_EVENT = ["0010", "0003", "1100", "00FF", "0202"]

FIXES = {
    "gen6:a/0/8/2:0055/00:00001": {
        "first_text": " проверил(а) компьютер, который папа подарил тебе.",
        "removed_count": 2,
        "reason": "The Russian wording is explicitly gender-neutral; the source 0x1100 English gender branches select fragments embedded across adjacent text and corrupt the neutral sentence if retained.",
    },
    "gen6:a/0/8/2:0055/00:00003": {
        "first_text": "…И ты уже без пижамы!",
        "removed_count": 1,
        "reason": "Russian wording avoids gender agreement; the source 0x1100 English gender branch selects fragments embedded across adjacent text and leaves a stray character if retained.",
    },
}


def main() -> int:
    rows = [json.loads(line) for line in TRANSLATIONS.open(encoding="utf-8")]
    found = set()
    for row in rows:
        spec = FIXES.get(row["record_id"])
        if spec is None:
            continue
        found.add(row["record_id"])
        segments = row["translation_segments"]
        prior_adjustments = row.get("control_adjustments", [])
        if prior_adjustments:
            if len(prior_adjustments) != spec["removed_count"] or spec["first_text"] not in "".join(
                    segment.get("text", "") for segment in segments):
                raise ValueError("Existing Milestone 3G adjustment differs from the expected correction")
            continue
        if row["record_id"].endswith(":00001"):
            if segments[0].get("control_words") != ["0010", "0002", "0100", "0000"]:
                raise ValueError("Unexpected player-name variable in PC record")
            if len([s for s in segments if s.get("control_words") == GENDER_EVENT]) != 2:
                raise ValueError("PC source control sequence changed; refusing blind rewrite")
            clear_index = next((i for i, segment in enumerate(segments)
                                if segment.get("control_words") == ["0010", "0001", "BE01"]), None)
            if clear_index is None:
                raise ValueError("PC dialogue clear event is missing")
            row["translation_segments"] = [segments[0], {"text": spec["first_text"]}, *segments[clear_index:]]
        else:
            if len(segments) != 3 or segments[1].get("control_words") != GENDER_EVENT:
                raise ValueError("Mirror source control sequence changed; refusing blind rewrite")
            row["translation_segments"] = [{"text": spec["first_text"]}]
        row["control_adjustments"] = [
            {"action": "remove_gender_selection", "control_words": GENDER_EVENT,
             "reason": spec["reason"]}
            for _ in range(spec["removed_count"])
        ]
        row["review_state"] = "draft_pending_owner_runtime_and_linguistic_review"
        row["review_note"] = "Corrected from owner-observed output after tracing the source player-name variable and 0x1100 gender-selection controls. Conditional English branches were removed because the Russian wording is gender-neutral; runtime recheck remains required."
        row["review_evidence"]["runtime_checked"] = False
        row["review_evidence"]["uncertainty"] = "Owner must verify both protagonist genders and line fit in AzaharPlus."
        row["status"] = "draft"
    if found != set(FIXES):
        raise ValueError(f"Missing expected correction records: {sorted(set(FIXES) - found)}")
    TRANSLATIONS.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
                            encoding="utf-8", newline="\n")
    print(json.dumps({"updated_records": sorted(found)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
