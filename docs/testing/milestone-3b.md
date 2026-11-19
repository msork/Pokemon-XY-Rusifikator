# Milestone 3B Validation Plan

## Automated checks

Run from the project root with all four local RomFS trees available:

```powershell
python scripts/extract_species_glossary.py
python scripts/build_translation_catalog.py
python scripts/build_pilot_translations.py
python scripts/validate_translation_data.py
python scripts/verify_text_roundtrips.py
python -m unittest discover -s tests -v
```

The species extractor reads a saved source-page copy under ignored `build/`, writes the UTF-8 species JSON, and checks 721 sequential National Dex IDs, unique English lookup names, NFC, and missing mappings. Translation tests use synthetic TextFiles and check protected variable/control sequences, untranslated variants, invalid Unicode, and species glossary lookup/consistency. The catalog scan is read-only and emits its data only to ignored `build/`; the scan report records unparsed, oversized, and non-TextFile inputs. The all-resource scan is not complete for the two oversized archives or other unsupported resource formats.

The translation validator compares each pilot row to the matching source coordinate and variant hash, checks ordered control words and placeholders, and reports catalog coverage. A PASS means the data structure is internally valid; it does not mean a translator reviewed the text, the translation has been tested in a game, or a build was installed.

## Owner runtime pilot procedure for a later milestone

No runtime test is requested or performed in Milestone 3B. After explicit approval and a separate disposable pilot build:

1. Back up the existing X/Y LayeredFS test archives and record their SHA-256 hashes.
2. Use a disposable save or a fresh game session; do not overwrite the owner's existing save.
3. With AzaharPlus 2126.2-A and update 1.5 enabled, inspect both X and Y separately.
4. Check early-game mother dialogue, the Serena/Calem greeting variant, Shauna's introduction, and Options > Text Speed.
5. Record line wrapping, name substitution, punctuation, spacing, control-event timing, menu fit, and any blank panels. Capture emulator screenshots/logs.
6. Restore the backups after the test and verify their hashes.

Never mark a draft `tested_in_game` without game-specific recorded evidence.
