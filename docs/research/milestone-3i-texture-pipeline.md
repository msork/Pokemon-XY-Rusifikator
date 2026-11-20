# Milestone 3I Texture Pipeline and Text Candidate

Date: 2026-11-20

## Scope and safety

Milestone 3I adds a local-only owner editing workflow for battle UI images and a separate uninstalled text candidate. It does not write to `workspace/`, saves, emulator folders, or installed mods. Generated PNGs and archive binaries are ignored under `build/milestone-3i/`. Do not commit or redistribute them.

The six button/HUD images are from `a/2/4/0`, GARC member `0/2`; the 18 type labels are from `a/2/3/9`, member `0/2`. Both are base resources in X and Y, byte-identical between games, and have no update 1.5 override in the extracted update trees. The resource hashes are in the canonical workspace manifest. In contrast, the string archive `a/0/7/4` is update 1.5-effective; the text candidate builder selects that update copy and uses base `a/0/8/2`, where no update copy exists.

## BCLIM encoding and internal pack rebuild

The verified editable image formats are BCLIM format 8 (RGBA4444) and format 9 (RGBA8888), with the original dimensions recorded per image. The encoder preserves source footer metadata, visible alpha, padded texels outside the visible image, and exact byte length. It uses the resource’s original tiled texture order and locates each BCLIM from the existing name/order table. The pack name/index table is preserved byte-for-byte; fixed dimensions/formats mean replacement BCLIM sizes do not change.

For RGBA4444, arbitrary edited 8-bit PNG channels are rounded to the nearest 4-bit channel. Maximum expected per-channel difference after decode is 8; original extracted PNGs use values representable exactly and pass byte-exact BCLIM identity checks. RGBA8888 stays channel-exact. PNG import accepts complete non-interlaced 8-bit RGBA PNGs, validates CRCs and filters 0–4, and rejects color-profile metadata so color conversion cannot be silently ignored. It also rejects changed dimensions and flattened/erased transparency.

The enclosing GARC member is LZ11-compressed. The new compressor emits literal-only LZ11 when a resource changes; the project decoder verifies the decompressed result. On a no-change build, the original compressed member is retained, allowing byte-exact archive identity. Changed builds preserve every unrelated GARC member’s original compressed bytes and validate the rebuilt GARC structure and texture pack after decompression. Emulator acceptance of changed image candidates remains untested.

Format assignments and tiled pixel storage were checked against the open-source [pk3DS BCLIM implementation](https://github.com/kwsch/pk3DS/blob/master/pk3DS.Core/CTR/Images/BCLIM.cs) (GPL-3.0). It was used as a format reference only; no code was copied. The project’s original encoder is separately covered by round-trip tests.

## Canonical owner-editing set

`python scripts/build_milestone3i_textures.py --init-editing-workspace` creates exactly one canonical set of 24 PNGs in `build/milestone-3i/editing/`. Filenames retain the original name plus `.png`, for example `fight_text.bclim.png`. `manifest.json` maps each PNG to its exact GARC path/member, texture order, original filename, dimensions, format, source archive/member hashes, alpha count, and initial PNG hash.

The six battle/HUD image names are `fight_text.bclim.png`, `bag_button.bclim.png`, `pokemon_button.bclim.png`, `run_button.bclim.png`, `ally_gauge.bclim.png`, and `enemy_gauge.bclim.png`. The remaining 18 are `type_icon_00_normal.bclim.png` through `type_icon_17_yousei.bclim.png`, with their exact original filenames listed in the manifest. The same canonical PNGs generate both X and Y candidates because source archive/member hashes are identical.

### Russian label specifications

These are proposed labels for image editing; the longest strings need a visual fit review inside their original 50×20 type-label canvases. Maintain the existing graphics, outline, anti-aliasing, color, and transparent areas.

| Source type | Proposed Russian image label |
|---|---|
| Normal | Обычный |
| Fighting | Боевой |
| Flying | Летающий |
| Poison | Ядовитый |
| Ground | Земляной |
| Rock | Каменный |
| Bug | Насекомый |
| Ghost | Призрачный |
| Steel | Стальной |
| Fire | Огненный |
| Water | Водный |
| Grass | Травяной |
| Electric | Электрический |
| Psychic | Психический |
| Ice | Ледяной |
| Dragon | Драконий |
| Dark | Тёмный |
| Fairy | Волшебный |

The other artwork labels are: FIGHT → `БОЙ`; BAG → `СУМКА`; POKÉMON → `ПОКЕМОНЫ`; RUN → `ПОБЕГ`; HP → `ОЗ`; level `Lv.` → `Ур.`. PP → `ОС` remains a dynamic text label and is not one of the 24 images. Check every replacement for legibility at game scale. Do not stretch, crop, flatten alpha, change canvas dimensions, or alter unrelated icon art.

## Backup, dry-run, candidate build, rollback

1. Create the canonical set once. The command refuses to overwrite a non-empty editing directory:

   `python scripts/build_milestone3i_textures.py --init-editing-workspace`

2. Before editing, make a workspace snapshot:

   `python scripts/build_milestone3i_textures.py --backup-editing-workspace`

   The command prints the hash-derived backup folder. To restore only those 24 PNGs and the source manifest:

   `python scripts/build_milestone3i_textures.py --restore-editing-backup build/milestone-3i/backups/<backup-id>`

   Restore verifies each backup hash and refuses a corrupt snapshot.

3. Before any edits, run the original-image dry-run:

   `python scripts/build_milestone3i_textures.py --dry-run`

   Outputs go to `build/milestone-3i/dry-run/`. It requires all 24 PNGs to match their original manifest hashes and verifies byte-identical BCLIMs, GARC archives, and unchanged members.

4. After artwork edits, optionally snapshot again, then run:

   `python scripts/build_milestone3i_textures.py --build-candidate`

   Original-image dry-run manifest SHA-256: `660eda6976972e41a282a93ebe4b054c441491084cd7e1fe6fca5b5bab414156`. Both X and Y resources were byte-identical to their inputs: `a/2/4/0` SHA-256 `5d5fce79754723726bd18271aeaed844c9c9a95f088076ad48de5cf66b22ecbb`; `a/2/3/9` SHA-256 `931a3ed9891533fd31a2ab2068f003fef1549cc72edd945104747b778ce4217c`. All 24 BCLIM files were byte-identical to source after PNG round-trip, with zero decoded-pixel difference.

   The generated, **uninstalled** LayeredFS candidates go to `build/milestone-3i/image-candidate/` with a SHA-256 manifest. If an output archive already exists, it is backed up beside the candidate as `.bak`; `candidate-backup-manifest.json` stores and verifies each backup hash. To restore prior candidate outputs or remove new ones:

   `python scripts/build_milestone3i_textures.py --rollback-candidate`

   This rollback only touches files below the generated image-candidate directory. It never operates on AzaharPlus mod paths.

5. The image candidate is not approved or tested in AzaharPlus. Do not install it until the owner has reviewed the images, the build hashes, and the remaining UI fit.

## Separate Milestone 3I text candidate

`python scripts/build_milestone3i_text_candidate.py` creates four ignored archives under `build/milestone-3i/text-candidate/`, with a manifest. It contains exactly 55 Milestone 3H draft records, 33 existing Milestone 3G battle drafts, and the two previously runtime-confirmed PC/mirror records, including the `проверил(а)` correction. Other early-game draft records are excluded. The candidate builder validates source hashes, control events, placeholders, untranslated messages, and unrelated GARC members through the existing rebuild pipeline.

The current deterministic output manifest hash is `6adfbc530804ec49977b521485564e60041f0cc6a8d4efd09424f3b5a5f838d9`. X and Y candidates are byte-identical for these shared resources: `a/0/7/4` SHA-256 `cf03806704b7b9117d8c5eaff49f419f7fb48f12710f992d8c0fa638fb78e6fa` (87 messages applied) and `a/0/8/2` SHA-256 `3b6a896334031dc197811b500ee3ff59749f941bf486fb53720ea7a7b2fb8bcb` (3 messages applied), covering all 90 records.

Generated hashes for the text candidate are reported in its manifest. The candidate is marked `runtime_tested: false` and `installed: false`. To remove only its four generated archives and Milestone 3I manifest:

`python scripts/build_milestone3i_text_candidate.py --rollback`

The text candidate does not include image changes. Image and text candidates must remain separately identifiable until the owner tests them independently.

## Keyboard work remains separate

The name-entry assets are in `a/0/1/9`, GARC entry `0/0`; its named BCLIM graphics are format 11 (ETC1A4), not supported by this 24-image encoder. Another `eng.bclim` in `a/2/3/9:0/2` is also format 11 and remains opaque. No keyboard artwork or input behavior is modified by Milestone 3I.

The name-entry layouts reference `nameinput1_lower.bclyt`, `nameinput2_lower.bclyt`, `nameinput_upper.bclyt`, and embedded font `cbf_std_kujira.bcfnt`. The key captions are drawn dynamically. Correct Cyrillic entry requires the executable’s key-index-to-character mapping, character-page switching, and supported character codes to agree with the visible labels. The project has only the extracted RomFS, not ExeFS/code, so it cannot verify or safely change those mappings. The current evidence does not establish that the embedded keyboard font has Ё/ё or the full Cyrillic alphabet. A separate future investigation must decode ETC1A4 images and identify input behavior before proposing any keyboard change.

## Automated validation

`tests/test_milestone3i.py` covers all 24 source-image byte-exact BCLIM round trips, byte-exact no-change X/Y GARC archives, PNG CRC/filter handling, RGBA4444 quantization and RGBA8888 identity, alpha/dimension rejection, texture pack/GARC rebuild preservation, LZ11 literal streams, editing-workspace backup/restore, candidate rollback, and scoped text candidate coverage. Runtime behavior and changed-image acceptance have not been tested in AzaharPlus.
