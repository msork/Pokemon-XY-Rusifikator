"""Locate local candidate bytes referenced by historical Windows install records."""

from pathlib import Path

from scripts.build_gameplay_pilot import GAMES


def recorded_candidate(candidate_root: Path, row: dict) -> Path:
    title_id, relative = row["relative_path"].split("/", 1)
    game = next(game for game, title in GAMES.items() if title == title_id)
    return candidate_root / game / relative
