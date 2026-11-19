# Milestone 3B: Translation Catalog and Gameplay Pilot

Date: 2026-11-19. Source RomFS trees are read-only. Catalog exports and scan reports are generated locally under ignored `build/` and `reports/` paths and are not distributable project data.

## Message identity and source inventory

The canonical location key is `resource path + GARC entry/subfile + TextFile message index`. A source variant is additionally keyed by the SHA-256 of the exact decoded little-endian 16-bit message words, including any terminator suffix where present. X/Y and base/update occurrences are combined only when both the coordinate and exact message-word hash match. Equal English strings at different coordinates remain separate records. A changed string at the same coordinate becomes a distinct source variant, retaining its own occurrence and provenance.

The all-member identity test found valid control-only records whose words end immediately after a complete length-prefixed control event, with no separate zero terminator. The parser now accepts this observed form for no-change rebuilds; byte-preserving replacements remain prohibited for a record without a source terminator suffix.

Each local JSONL source row records the coordinate ID, source-variant hash, word count, decoded text and ordered text/control segments, raw control words, archive/member/TextFile hashes, and every game/version occurrence. Variable events retain their complete word sequence, including zero-valued arguments. The export is derived copyrighted source text and stays under ignored `build/`; only project-authored Russian pilot records are eligible for Git.

`python scripts/build_translation_catalog.py` scans the four RomFS roots read-only for GARC v4 signatures and attempts bounded LZ11/TextFile parsing for each member. The run report states scan counts and any archives skipped over 128 MiB; those archives are explicitly outside this scan's verified TextFile coverage. Candidate resources independently verified during Milestone 2A remain:

| Resource | Base | Update 1.5 | Parsed message counts per game |
|---|---|---|---:|
| `a/0/7/4` | 151 TextFiles | 151 TextFiles | 27,605 base; 27,607 update |
| `a/0/8/2` | 424 TextFiles | absent | 7,607 base |

The four known resources match byte-for-byte between X and Y for corresponding versions. The update text archive has two added message coordinates and two changed messages at existing coordinates relative to base. Runtime selection of the effective update resource is covered by the AzaharPlus owner-confirmed LayeredFS tests documented in Milestones 2C/2D; the catalog still preserves both source versions.

The generated scan report is `reports/milestone-3b/asset-catalog.json`. The corrected run scanned 1,600 files, found 568 GARC-signature candidates, parsed 566 under the cap, and recognized 11,616 TextFile members containing 1,005,104 occurrences. Exact coordinate/source-word deduplication produced 281,728 source variants. Duplicate-text analysis found 30,344 repeated-text groups spanning 132,997 records; these records retain their distinct coordinates. Two 1,041,219,296-byte archives, `pokemon-x/base/a/0/0/7` and `pokemon-y/base/a/0/0/7`, exceeded the 128 MiB cap and were skipped by the full-catalog parser. A read-only memory-mapped header/index check confirmed each contains 7,852 members with numerous compressed/binary signatures, but a full member decompression pass was stopped for resource cost. Their text coverage remains unverified. The report includes 66,666 member parse rejections with path and magic; these are non-TextFile formats or unsupported candidate structures, not proof that the members are corrupt. The generated source catalog is 502.27 MiB. Neither generated file belongs in Git. Coverage is limited to GARC members accepted by the current parser as TextFiles; the two skipped archives, executable literals, and other resource formats are not yet covered.

## Translation record and validation

The translation database separates source catalog (local/ignored) from authored translations (`translations/`). Stable message IDs do not depend on text or translation. Each translation row specifies `record_id`, source variant hash, game scope (`shared`, `x`, or `y`), version scope (`base`, `update-1.5`, or both), ordered Russian text/control segments, and status (`untranslated`, `machine_draft`, `reviewed`, `validated`, or `tested_in_game`). The validator compares both scopes to actual source provenance. Different source text at the same coordinate uses a different source variant hash, enabling a translation override without conflating it with the unchanged game/version record. Pilots in this milestone are drafts only. They are not runtime-tested or human-reviewed.

The validator rejects unknown/duplicate IDs, stale source hashes, malformed segments, altered/reordered control or placeholder words, non-NFC text, unsupported non-BMP/surrogate/control characters, and records with invalid status. It checks English species-name occurrences against the canonical species glossary and flags drafts that omit the official source spelling; dynamic names and inflection can require a human exception. Expansion over 2.5 times the English source length is flagged as suspicious, not treated as an engine limit. Runtime observations in [Milestone 3A](milestone-3a.md) are only that the 295-word and 350-word test panels rendered and the 527-word panel went blank in both games; these are test outcomes, not universal text limits.

## Pokémon species glossary and attribution

`glossary/pokemon_species_ru.json` contains 721 entries in National Pokédex order, extracted from [Bulbapedia's Russian Pokémon names list](https://bulbapedia.bulbagarden.net/wiki/List_of_Russian_Pok%C3%A9mon_names), revision 4640552, retrieved 2026-11-19. The page describes the Cyrillic column as the official Russian spellings and distinguishes the BGN/PCGN romanization column as informational. English names map to the source's current Cyrillic spelling; National Dex number is the stable key. The extractor validates contiguous IDs #0001–0721, unique English lookup keys, presence of mappings, and NFC.

Attribution: Bulbapedia contributors, “List of Russian Pokémon names,” revision 4640552, https://bulbapedia.bulbagarden.net/wiki/List_of_Russian_Pok%C3%A9mon_names. The dataset is licensed separately from project code under [Creative Commons Attribution-NonCommercial-ShareAlike 2.5 Generic](https://creativecommons.org/licenses/by-nc-sa/2.5/). Bulbapedia's [copyright statement](https://bulbapedia.bulbagarden.net/wiki/Bulbapedia:Copyright_policy) requires attribution, non-commercial use, and ShareAlike for covered article content. This dataset must retain that license and attribution when redistributed; WTFPL does not apply to it. The source's Pokémon trademark disclaimer also means this license does not grant Nintendo/Game Freak trademark or game-asset rights. Do not bundle the dataset into a commercial release.

The page contains two historical-name tables. The handbook comparison contains 45 rows, matching its accompanying prose. The former official Pokédex/Champion's Handbook II comparison table contains 64 rows in the saved revision, while its prose states 66. This discrepancy is retained as a source note; the extractor records only the 64 rows actually present and does not infer two missing names. Historical alternatives are separately labeled and must not override current names.

The structured glossary's current mappings are all marked `established_official_per_source`, not as independently verified game-localization choices. The validator confirms 721 unique English names, 721 unique current Russian spellings, contiguous National Dex IDs, and NFC-normalized text. A missing or conflicting source name must remain flagged for review and must never be fabricated. Species references in translations should resolve through National Dex identity, then the current Russian glossary spelling; the source romanization and historical alternatives are reference-only.

## Terminology status

`glossary/terms.json` provides categorized UI, location, character, move, ability, and item terms. Initial UI/character/place-name suggestions are explicitly `provisional_review_required`; move, ability, and item seeds have no Russian value and are marked `needs_research`. These are research tasks, not English fallback or permission to invent a term. Translation memory/glossary enforcement should run against current entries and flag unresolved terms for review.

## Pilot messages

The pilot file `translations/pilot.jsonl` contains only selected early-game story and options messages, keyed by the canonical stable IDs and source-variant hashes. All entries remain `machine_draft`. The story set includes the player's mother, Serena/Calem greetings, and Shauna's meeting; it tests names, a player-name variable, line breaks, and control events. The options set tests short UI labels and an explanatory string. The source export contains the English context; the committed translation file does not duplicate full English archives/text exports.

Pilot coordinates (X/Y sources were identical for these records):

| Resource | Member | Message IDs | Context |
|---|---:|---|---|
| `a/0/8/2` | `55/0` | 10, 13 | Mother's morning greeting and send-off |
| `a/0/8/2` | `57/0` | 1, 2, 3, 6 | Serena, Calem, and Shauna introductions |
| `a/0/7/4` | `75/0` | 0, 3, 4, 5, 6, 7 | Options title, text speed labels, explanation |

Proposed owner procedure after a later approved test build: load a disposable save or start a fresh game without overwriting an existing save; compare the selected story and Options messages in both games; record X/Y separately; inspect line breaks, names, variable substitution, and menu fit; retain emulator logs/screenshots and mark only confirmed records `tested_in_game`. No pilot patch was installed or runtime-tested during this milestone.

## Reproducibility and limits

- Regenerate the species file from the locally saved source page with `python scripts/extract_species_glossary.py`.
- Regenerate the local message catalog with `python scripts/build_translation_catalog.py`.
- Build the twelve draft records with `python scripts/build_pilot_translations.py`.
- Validate the glossary and pilot against the ignored local catalog with `python scripts/validate_translation_data.py`.
- Run `python -m unittest discover -s tests -v`.
- Source datasets are read-only; generated extraction catalogs/reports remain ignored.
- This milestone does not bulk translate, rebuild a release archive, install a patch, or claim complete text discovery beyond reported parser coverage.
