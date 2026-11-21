# Milestone 3M Artwork Build and Installation

## Scope

Milestone 3M rebuilt the owner's 24 canonical RGBA PNG edits in `build/milestone-3i/editing/` into the two battle UI GARC resources for each game. The canonical PNGs and their manifest were hash-checked before and after generation; the build script refuses to proceed if their bytes change. The archives were rebuilt from the effective resources available in the extracted datasets. Both target resources are from the base RomFS because neither is present in either v1.5 update tree; the update-enabled games therefore use the base fallback for these two paths.

The 24 changed BCLIMs retain their original internal filenames, dimensions, resource formats, pack order, alpha channel, and GARC member mapping. The generated archive rebuilds preserve all non-target textures and GARC members. Three independent builds produced matching hashes. Forty-eight decoded previews (24 per game) are in `build/milestone-3m/decoded-previews/`.

## Installed artifacts

AzaharPlus mod root: `%APPDATA%\AzaharPlus\load\mods`.

| Game | Title ID | Resource | SHA-256 | Size |
| --- | --- | --- | --- | ---: |
| Pokémon X | `0004000000055D00` | `a/2/3/9` | `5f1f1ee312ee793417ad9808c733649791e9cb2e56ab5279bd66b44297399226` | 297,844 |
| Pokémon X | `0004000000055D00` | `a/2/4/0` | `ea90b16d693df77b86d935383207d9a02bcd6728534999be0f59d80464d1a9a0` | 1,383,016 |
| Pokémon Y | `0004000000055E00` | `a/2/3/9` | `5f1f1ee312ee793417ad9808c733649791e9cb2e56ab5279bd66b44297399226` | 297,844 |
| Pokémon Y | `0004000000055E00` | `a/2/4/0` | `ea90b16d693df77b86d935383207d9a02bcd6728534999be0f59d80464d1a9a0` | 1,383,016 |

The source texture pack was identical between X and Y for both resources, so corresponding X/Y archives match. The `a/2/3/9` archive was installed because its 18 edited type-label PNGs are part of the canonical set. No other archive was installed.

## Backup and preservation verification

Installation record: `build/milestone-3m/installation/installation-record.json`.

Backup manifest: `build/milestone-3m/installation/installation-backups/20261121T074006Z/manifest.json`.

- Both pre-existing `a/2/4/0` targets were backed up at SHA-256 `1becfbb516f81ce2f885490b9dfba6b2404524b7b1cf87e0669cdba56f58fc0e`.
- Both `a/2/3/9` targets were absent before installation; rollback removes only those paths.
- The four installed Milestone 3K text archives were verified before and after installation and remain unchanged: `a/0/7/4` is `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e`; `a/0/8/2` is `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` for both games.
- Saves, extracted game assets, updates, and unrelated mod files were not modified.
- AzaharPlus was not launched; runtime rendering is unverified.

## Rollback

Close AzaharPlus before rolling back. From the project root, run:

```powershell
python scripts/install_milestone3m_images.py --rollback
```

The rollback checks that installed image hashes still match the Milestone 3M record and that all four Milestone 3K text files remain intact. It restores the backed-up X/Y `a/2/4/0` files and removes only the two `a/2/3/9` files recorded as originally absent. It refuses to proceed if an installed target or backup has changed. The older Milestone 3L record and backup remain separate and are not overwritten.

## Owner runtime check

With update 1.5 enabled, launch X and Y separately and inspect the battle command screen, battle status display, move selection, and type labels. Check the Russian artwork for clipping, alignment, transparency artifacts, and legibility. This project has not performed those runtime checks.
