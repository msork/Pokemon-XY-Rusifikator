# Milestone 3J: Integrated Artwork and Text Candidate

## Scope and safety

This milestone prepares owner-editable battle artwork references and rebuild candidates. It did not install files, launch AzaharPlus, modify saves, or write to `workspace/`. Generated images, candidate archives, and manifests remain under ignored `build/` directories and must not be committed.

## Artwork workspace and reference sheets

The canonical 24-PNG workspace is `build/milestone-3i/editing/`, described by its `manifest.json`. The manifest SHA-256 is `17241e3dd9739a463df73c7c07d22113997066c958d77bbed9aafa36ebcbd22e`. The workspace validator found all 24 expected assets with matching dimensions, RGBA8 data, both transparent and opaque pixels, and supported BCLIM source formats 8 or 9. The validation command is read-only:

```powershell
python scripts/build_milestone3i_textures.py --validate-editing-workspace
```

The English-labeled contact sheet and Russian-label reference sheet are generated under `build/milestone-3j/artwork-reference/`:

- `contact-sheet-english.svg` — source labels and asset identity.
- `contact-sheet-russian-reference.svg` — translation specifications only; it does not alter artwork.

The sheets embed the original PNG bytes and display each resource/member coordinate, internal filename, dimensions, BCLIM format, pack order, and PNG hash prefix. Their SHA-256 values are recorded in the generated `manifest.json` in that directory. Russian label specifications are: FIGHT → БОЙ; BAG → СУМКА; POKÉMON → ПОКЕМОНЫ; RUN → ПОБЕГ; HP → ОЗ; Lv. → Ур.; and the 18 established type labels shown on the Russian sheet.

The owner should edit only these canonical PNGs:

```text
build/milestone-3i/editing/ally_gauge.bclim.png
build/milestone-3i/editing/bag_button.bclim.png
build/milestone-3i/editing/enemy_gauge.bclim.png
build/milestone-3i/editing/fight_text.bclim.png
build/milestone-3i/editing/pokemon_button.bclim.png
build/milestone-3i/editing/run_button.bclim.png
build/milestone-3i/editing/type_icon_00_normal.bclim.png
...
build/milestone-3i/editing/type_icon_17_yousei.bclim.png
```

Use an editor/export option that preserves PNG RGBA 8-bit color, original pixel dimensions, and alpha. Do not resize, flatten transparency, convert to indexed color, or add color-profile chunks. Validate exports before encoding. BCLIM format 9 retains 8-bit channels; format 8 stores RGBA4444 and therefore quantizes channels to 4 bits. Exact BCLIM bytes are expected only for unchanged artwork; changed format-8 art is compared after decode, with a maximum per-channel quantization delta of 8. The existing regression suite covers PNG CRC/filter decoding, alpha, dimensions, BCLIM encode/decode, texture ordering, pack rebuilding, and no-change byte-exact archive round trips.

## Integrated text candidate

`scripts/build_milestone3j_text_candidate.py` combines the four existing source catalogs without overwriting a row:

| Catalog | Records |
| --- | ---: |
| `translations/pilot.jsonl` | 12 |
| `translations/early-game.jsonl` | 127 |
| `translations/milestone3g-battle.jsonl` | 33 |
| `translations/milestone3h-ui-battle.jsonl` | 55 |
| **Total** | **227** |

The builder rejects any repeated record ID. It distinguishes an identical-ID duplicate from a duplicate whose `source_variant_sha256` differs and aborts the build in either case; no earlier record is selected silently. Current inputs have 227 unique IDs and no duplicates or source-hash conflicts. Source file hashes and translation status counts are included in the candidate manifest. Drafts are explicitly included for runtime testing and remain unapproved.

For each game and resource, the builder selects the update 1.5 file if it exists, otherwise the base file; it does not merge the trees. Each record must match its source hash, game scope, version scope, control-event sequence, and supported encoding. The GARC rebuild verifies byte-exact no-change parsing, unchanged unrelated members, unchanged untranslated messages, and translated message words. Both X and Y candidates are built separately even when their resulting hashes match.

Build the text candidates with:

```powershell
python scripts/build_milestone3j_text_candidate.py
```

Outputs are under `build/milestone-3j/text-candidate/`, at per-game LayeredFS-relative paths. The generated manifest records source versions and SHA-256 values. Remove only these generated candidates or restore their prior generated state with:

```powershell
python scripts/build_milestone3j_text_candidate.py --rollback
```

The rollback command verifies any builder-created backup hash before restoring it. It applies only within the generated candidate directory and does not touch emulator mods.

## Candidate build and rollback commands

After manual PNG edits, validate and build a separate image candidate:

```powershell
python scripts/build_milestone3i_textures.py --validate-editing-workspace
python scripts/build_milestone3i_textures.py --build-candidate
```

The image candidate is written to `build/milestone-3i/candidate/`; its manifest records per-resource hashes and backup data for prior generated candidates. `--rollback-candidate` restores/removes generated candidate files only. To rebuild an unmodified dry run without an image candidate:

```powershell
python scripts/build_milestone3i_textures.py --dry-run
```

Keep image and text candidates independently testable. Do not combine, install, or copy them to AzaharPlus until their separate manifests pass review and an owner authorizes runtime testing. Existing emulator mods are outside these scripts; if installation is authorized later, back up each target first, record absent targets, verify the installed hashes, and roll back only those exact targets from verified backups.

## Runtime and linguistic status

No 3J candidate has been installed or runtime-tested. The Russian label strings are owner artwork specifications, not proof of visual fit or localization quality. The contact sheets are reference aids, not replacement images. The integrated text candidate contains runtime-test drafts and earlier records in their existing status; inclusion is not human approval.

## Reproducible candidate hashes

The generated text manifest reports 227 unique source records: 12 machine drafts and 215 drafts. Input SHA-256 values are `c1cc551bb7978ba20daceb529081384d4b7fba314a63a0988dd6eebdf536a437` (`pilot.jsonl`), `a344a5e108b3d8554cd31620af78225572dc97ec80c1e81f30b3a77e3fb8abff` (`early-game.jsonl`), `b358e343067270fec5d8cadc6655dc29003514bea20c345c8c0f222522c9aa20` (Milestone 3G), and `b2746a934014919b19474f0dfc94a52bf171d546af2687b8a3ee55b3369cc295` (Milestone 3H). No duplicate IDs or source-hash conflicts were found.

| Game | Resource | Effective input | Source SHA-256 | Candidate SHA-256 | Applied records |
| --- | --- | --- | --- | --- | ---: |
| X | `a/0/7/4` | Update 1.5 | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e` | 125 |
| X | `a/0/8/2` | Base fallback | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` | 102 |
| Y | `a/0/7/4` | Update 1.5 | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` | `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e` | 125 |
| Y | `a/0/8/2` | Base fallback | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` | `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` | 102 |

Each resource proof also records 120 unchanged unrelated GARC members and 9,829 unchanged untranslated messages for `a/0/7/4`, and 419 unrelated members and 80 untranslated messages for `a/0/8/2`. The matching X/Y hashes reflect equal selected source bytes and current shared translations; X and Y were built independently. Runtime remains untested.
