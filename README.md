# Pokémon X/Y Rusifikator

An English-documented, specification-driven project for a Russian localization of Pokémon X and Pokémon Y, targeting Azahar on Windows. The project is in discovery and architecture; no translated patch is available yet.

## Safety

The extracted game data in `workspace/` is local source material. It is read-only and intentionally excluded from Git. This repository must not contain game images, extracted archives, saves, or complete modified game binaries. Any eventual release must be reviewed for an appropriate delta-only distribution format.

## Current milestone

Milestone 1 establishes the architecture and inventories the four local datasets. Run the read-only inventory utility from the repository root:

```powershell
python scripts/inventory.py inventory workspace/pokemon-x/base reports/pokemon-x-base.jsonl
python scripts/inventory.py compare workspace/pokemon-x/base workspace/pokemon-y/base
python -m unittest discover -s tests -v
```

The manifests contain relative paths, sizes, and SHA-256 hashes. They are local generated reports and are not committed.

## Project layout

- `docs/architecture/`: pipeline and component boundaries.
- `docs/specifications/`: inventory, provenance, and translation data contracts.
- `docs/research/`: evidence and source references.
- `docs/testing/`: validation and runtime test plans.
- `docs/release/`: packaging and recovery requirements.
- `scripts/`: deterministic read-only and build utilities.
- `tests/`: tests using synthetic fixtures only.
- `glossary/`, `translations/`: future terminology and translation records.
- `workspace/`: local read-only RomFS datasets; never commit.

See [the architecture overview](docs/architecture/overview.md) and [research log](docs/research/milestone-1.md).
