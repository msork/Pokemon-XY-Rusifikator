# Milestone 3J Owner Artwork Workflow

## Reference material

Open these generated SVGs in a browser or vector-capable image viewer:

- `build/milestone-3j/artwork-reference/contact-sheet-english.svg`
- `build/milestone-3j/artwork-reference/contact-sheet-russian-reference.svg`

The first sheet identifies each English-labeled source asset. The second lists Russian label specifications while showing the same original PNGs; neither sheet is game artwork.

## Canonical PNG files for manual editing

Edit the following files in place; do not rename or add files:

```text
build/milestone-3i/editing/ally_gauge.bclim.png
build/milestone-3i/editing/bag_button.bclim.png
build/milestone-3i/editing/enemy_gauge.bclim.png
build/milestone-3i/editing/fight_text.bclim.png
build/milestone-3i/editing/pokemon_button.bclim.png
build/milestone-3i/editing/run_button.bclim.png
build/milestone-3i/editing/type_icon_00_normal.bclim.png
build/milestone-3i/editing/type_icon_01_kakutou.bclim.png
build/milestone-3i/editing/type_icon_02_hikou.bclim.png
build/milestone-3i/editing/type_icon_03_doku.bclim.png
build/milestone-3i/editing/type_icon_04_jimen.bclim.png
build/milestone-3i/editing/type_icon_05_iwa.bclim.png
build/milestone-3i/editing/type_icon_06_mushi.bclim.png
build/milestone-3i/editing/type_icon_07_ghost.bclim.png
build/milestone-3i/editing/type_icon_08_hagane.bclim.png
build/milestone-3i/editing/type_icon_09_honoo.bclim.png
build/milestone-3i/editing/type_icon_10_mizu.bclim.png
build/milestone-3i/editing/type_icon_11_kusa.bclim.png
build/milestone-3i/editing/type_icon_12_denki.bclim.png
build/milestone-3i/editing/type_icon_13_esper.bclim.png
build/milestone-3i/editing/type_icon_14_koori.bclim.png
build/milestone-3i/editing/type_icon_15_dragon.bclim.png
build/milestone-3i/editing/type_icon_16_aku.bclim.png
build/milestone-3i/editing/type_icon_17_yousei.bclim.png
```

Retain each file's original pixel dimensions and RGBA8 PNG mode with transparent and opaque pixels. Avoid indexed color, alpha flattening, resizing, color-profile chunks, and filename changes. Format-8 texture encoding quantizes channels to RGBA4444; format-9 encoding retains RGBA8888. Candidate validation reports the applicable format for each asset.

## Validate and rebuild after editing

From the repository root, run:

```powershell
python scripts/build_milestone3i_textures.py --validate-editing-workspace
python scripts/build_milestone3i_textures.py --build-candidate
```

Validation is read-only. The image builder writes only the separate candidate directory `build/milestone-3i/candidate/`, never the canonical source PNGs, game workspace, or emulator folders. Review `build/milestone-3i/candidate/manifest.json` and compare its hashes before any later runtime-test request. Restore or remove generated candidate outputs with:

```powershell
python scripts/build_milestone3i_textures.py --rollback-candidate
```

Do not copy candidate files into AzaharPlus as part of this workflow. Image and text candidates remain separate; the integrated text candidate is built independently with:

```powershell
python scripts/build_milestone3j_text_candidate.py
```

That candidate is under `build/milestone-3j/text-candidate/`. Its rollback command affects only that generated directory:

```powershell
python scripts/build_milestone3j_text_candidate.py --rollback
```

## Installation status

No files were installed for Milestone 3J. These build commands do not launch AzaharPlus or write to its user-data directory. Future installation requires separate authorization and a fresh backup/hash record for each exact LayeredFS target; runtime success must be recorded independently for Pokémon X and Pokémon Y.
