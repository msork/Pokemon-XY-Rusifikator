# Milestone 3N Texture Discovery

## Scope and safety

The discovery utility reads only the four extracted source trees under `workspace/pokemon-x/{base,update-1.5}` and `workspace/pokemon-y/{base,update-1.5}`. All PNGs, manifests, contact sheets, and reports are generated under the ignored `build/milestone-3n/editing/` directory. No source archive or game asset was edited, and no extracted or generated commercial asset is part of the Git change set.

Run with:

```powershell
python scripts/scan_milestone3n_artwork.py
```

The generated `texture-manifest.json` and `.csv` keep a row for every source occurrence, including game, base/update version, archive path, outer/nested GARC member, internal texture filename, dimensions, BCLIM format, raw-resource SHA-256, candidate English evidence, review confidence, deduplicated image ID, and canonical PNG path. Identical raw texture bytes share a single metadata-free RGBA PNG while every source mapping remains in the manifest. Contact sheets are divided by filename/path-derived category and numbered with the manifest asset ID.

Every successfully decoded BCLIM encountered by the scanner is exported, not only resources whose names appear English. This intentionally over-includes images for manual inspection. `suggested_russian_translation` remains blank; new artwork has not been translated. Filename English tokens are hints only, not OCR evidence.

## Parser and decoder evidence

- The project GARC v4 parser recognizes the `CRAG` signature and members; read-only mmap inspection is used for large source archives to avoid holding whole archives and all decoded images in memory simultaneously.
- Members with the 3DS `0x11` LZ format are decompressed before searching for nested GARC and texture-pack structures.
- Named BCLIM entries are located through the pack index and `CLIM` footer. The reused local decoder exports BCLIM formats 7, 8, and 9 to RGBA PNG. Format 8/9 round-trip validation remains covered by the existing Milestone 3I tests.
- The Milestone 3M canonical edit targets are the exact 6 `a/2/4/0` textures and 18 `a/2/3/9` type labels listed in `build/milestone-3i/editing/manifest.json`; their own formats are 8 or 9. Milestone 3M decodes all 24 per game to 48 previews.
- BCH embedded texture decoding is not implemented. The scan records BCH magic occurrences in uncompressed source-file bytes where scanned, but it does not parse BCH containers or extract their embedded textures.

The scan is not exhaustive. GARC members larger than 128 MiB are reported and left unmaterialized for safety. Other container/compression formats, unknown texture packs, BCH texture payloads, layouts, and any binary data not recognized by the current signatures remain unresolved. OCR was not run because no OCR executable or library was available during this run. The manifest therefore marks candidates for visual review rather than asserting their text is English.

## Scan results (2026-11-21)

| Measure | Result |
| --- | ---: |
| Source files visited (four datasets) | 1,600 |
| Source bytes read | 3,624,704,206 |
| GARC source bytes SHA-256 verified | 3,218,038,304 |
| GARC files / unique GARC hashes | 568 / 288 |
| GARC members inspected | 93,986 |
| LZ11 members decoded | 29,566 |
| Texture packs recognized | 5,548 |
| BCLIM entries encountered | 13,040 |
| BCLIM entries decoded to PNG | 8,608 |
| Unique raw texture hashes / PNG files | 3,575 |
| Duplicate source occurrences represented in the manifest | 5,033 |
| M3I already-translated occurrences excluded from the pending queue | 48 |
| Contact sheets | 50 |

Decoded occurrences came from X base (4,291), Y base (4,291), and each v1.5 update (13 each). The 48 M3I exclusions are the canonical six battle/HUD assets and 18 type labels in the X/Y base resources. Every remaining decoded texture is marked `manual_review_pending`; that is a visual review queue, not a claim that each image contains English.

The decoder exported BCLIM formats 7, 8, and 9. It recorded 4,432 BCLIM decode failures: formats 0 (82), 2 (26), 3 (248), 5 (398), 6 (62), 10 (476), 11 (3,046), 12 (70), and 13 (6), plus 18 unsupported storage/dimension layouts. The most significant gap is format 11, which needs a verified ETC decoder before those assets can be previewed. Format 12/13 decoding also remains unavailable. The scanner additionally logged 4,876 suspected `CLIM`-bearing members whose texture-pack index could not be accepted; these may include false signature matches and are unresolved rather than silently excluded.

The report lists 9,372 unsupported or failed occurrences in total, including LZ11 decode errors (34 member cases plus two top-level cases), texture-pack/index failures, unsupported BCLIM formats, and storage-layout mismatches. There were 24 `BCH` magic occurrences in raw non-GARC source files; this count does not inspect compressed GARC member contents for BCH signatures and is not a BCH resource inventory. The utility currently does not decode BCH-embedded textures or parse layouts. `scan-report.json` contains the complete per-case error list and separates scan coverage from successfully exported PNGs.

The 50 sheets are grouped by filename/path heuristics: unclassified manual review (39), battle (3), menu (2), and one each for keyboard, logo/title, map/sign, Pokédex, shop/bag, and social assets. Those buckets guide review and do not guarantee content classification. OCR was not available; the candidate text field contains filename-token hints only, and the Russian suggestion field is intentionally empty.

## Third-party research references

The Gen VI tool ecosystem confirms that BCLIM and ETC1/ETC1A4 are relevant formats and that texture decoding support varies by tool. Candidate primary-source implementations for follow-up research include [pk3DS BCLIM implementation](https://github.com/kwsch/pk3DS/blob/master/pk3DS/3DS/BCLIM.cs), [png2bclim BCLIM implementation](https://github.com/kwsch/png2bclim/blob/master/png2bclim/BCLIM.cs), and [3DSkit](https://github.com/Tyulis/3DSkit). No code from these repositories was copied into this milestone. Their licenses and exact compatibility must be reviewed before reuse. The current scanner explicitly reports formats it cannot decode instead of treating them as PNG exports.

## Manual review workflow

Open `contact-sheets/` first, then use the `asset_id` to locate all occurrences in the JSON/CSV. Edit only copies in a separately named manual-edit directory; do not replace generated discovery PNGs or source RomFS data. After an artwork is approved, a resource-specific rebuild must preserve the original internal name, pack order, dimensions, format, transparency, and unrelated GARC members, then produce an independently tested X/Y candidate and backup/rollback record. Nothing discovered in Milestone 3N has been rebuilt or installed.
