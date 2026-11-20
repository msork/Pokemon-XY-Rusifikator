# Milestone 3I Owner Image Editing and Test Instructions

This milestone has not installed any image or text candidate. Work only with the generated files under `build/milestone-3i/`; do not place output in an AzaharPlus mod folder.

## Editing the canonical images

1. Run `python scripts/build_milestone3i_textures.py --init-editing-workspace` once.
2. Review `build/milestone-3i/editing/manifest.json`. It is the authoritative mapping from each PNG to its resource, GARC member, internal filename, dimensions, format, and original hashes.
3. Run `python scripts/build_milestone3i_textures.py --backup-editing-workspace` before editing and keep the printed backup ID.
4. Edit the 24 top-level `.png` files only. Keep the existing canvas size and transparency. Export as non-interlaced 8-bit RGBA PNG with no embedded color profile. Avoid indexed-color, RGB-only, cropped, or resized output.
5. Keep replacement art aligned and readable at the original 3DS screen scale. The 18 type labels use 50×20 canvases; several Russian names may need condensed lettering. Keep each separate type icon and do not combine them into a sprite sheet.
6. Run `python scripts/build_milestone3i_textures.py --build-candidate`. Review the output manifest’s source/output hashes, per-image decoded-pixel checks, alpha counts, and unchanged-member counts.
7. This only builds candidate files. Do not install them as part of this step.

To restore the editing images from a snapshot, use `python scripts/build_milestone3i_textures.py --restore-editing-backup build/milestone-3i/backups/<backup-id>`. To roll back generated image candidates, use `python scripts/build_milestone3i_textures.py --rollback-candidate`.

## Labels to draw

- Battle commands: `БОЙ`, `СУМКА`, `ПОКЕМОНЫ`, `ПОБЕГ`.
- Gauges: `ОЗ` for HP and `Ур.` for Lv.
- Move types: Обычный, Боевой, Летающий, Ядовитый, Земляной, Каменный, Насекомый, Призрачный, Стальной, Огненный, Водный, Травяной, Электрический, Психический, Ледяной, Драконий, Тёмный, Волшебный.
- PP uses `ОС` as dynamic text; it is not in the image set.

Check lettering against the original PNGs and the Russian text glossary. A correct translation can still be too wide for a texture. Return the edited PNGs or the generated candidate manifest for review before any installation.

## Text-only candidate

Run `python scripts/build_milestone3i_text_candidate.py` to build a separate candidate with 55 Milestone 3H drafts, existing Milestone 3G battle drafts, and the two tested PC/mirror messages. It is not installed or runtime-validated. Remove it with `python scripts/build_milestone3i_text_candidate.py --rollback`.

## Later owner runtime test

After separate review/authorization to install candidates, test image and text candidates independently in X and Y with update 1.5 enabled. Capture screenshots of command buttons, ally/enemy gauges, all type labels visible in move selection, name/nickname screens, PC/mirror dialogue, battle text, and the Prof’s Letter acquisition. Report game/version and exact screen for each screenshot. Do not infer Y results from X.
