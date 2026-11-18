# AzaharPlus 2126.2-A Test Plan

## Target profile

- Windows installation: `C:\Users\maxim\Games\azaharplus-2126.2-A-windows`
- Observed user data: `%APPDATA%\AzaharPlus`
- Pokémon X mod root: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs`
- Pokémon Y mod root: `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs`
- Run with each game's update 1.5 enabled. LayeredFS folders use the base game Title IDs.

## Milestone 2C language-selection screen probe

The user-provided X and Y screenshots show the initial language-selection interface. Source inspection locates the visible screen strings in `a/0/7/4`, GARC member 85/0, including message 1 (help panel), message 4 (game title), and messages 6-12 (language names). The visible bottom-right `Ver. 1.5` is message 25 in that same member in update 1.5. Base member 85 has messages 0-24 and no message 25. This explains why the earlier probe of member 35/0 message 22 could not change the screenshot: it targeted a separate duplicate label that is not the one rendered on this screen.

The new builder creates two variants from the update 1.5 archive for both games:

- ASCII control: `ASCII 2C`
- Russian rendering probe: `Привет!`

Both replace only message 25 in member 85/0, retain its empty control-code signature and message ID, and preserve the other 150 GARC members byte-for-byte. Generated outputs are under ignored `build/milestone-2c/`. Run `python scripts/build_language_screen_poc.py` to regenerate them.

### Safe manual runtime sequence

Do not install either variant until ready to run the test. Close AzaharPlus before changing a mod file. The earlier Milestone 2B output may already be present at the exact target. Preserve that file before replacing it, and do not delete or overwrite any other mod files.

In PowerShell from the project root, copy the two currently installed files to a backup directory. The commands stop if either source is missing or either backup already exists:

```powershell
$backup = Join-Path $env:TEMP 'pokemon-xy-milestone-2c-backup'
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
if (!(Test-Path -LiteralPath $xTarget) -or !(Test-Path -LiteralPath $yTarget)) { throw 'Expected installed Milestone 2B files were not found; inspect mod directories before proceeding.' }
$xBackup = Join-Path $backup 'pokemon-x-a074'
$yBackup = Join-Path $backup 'pokemon-y-a074'
if ((Test-Path -LiteralPath $xBackup) -or (Test-Path -LiteralPath $yBackup)) { throw 'A backup already exists; choose a new backup directory.' }
Copy-Item -LiteralPath $xTarget -Destination $xBackup
Copy-Item -LiteralPath $yTarget -Destination $yBackup
```

Install the ASCII control for X first. Verify the project-root working directory and generated file before copying:

```powershell
$source = (Resolve-Path '.\build\milestone-2c\ascii-control\pokemon-x\0004000000055D00\romfs\a\0\7\4').Path
$target = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
Copy-Item -LiteralPath $source -Destination $target -Force
```

Launch Pokémon X with update 1.5 enabled and check the bottom-right label:

- `ASCII 2C` means the LayeredFS replacement is visible and the update-only message 25 is selected.
- `Ver. 1.5` means this run did not observe the replacement. Recheck the title ID folder, target path, update selection, emulator restart, and other mods that may supply the same resource. Do not infer a font problem from this result.

Close the emulator. Repeat the ASCII control with Y by using `build\milestone-2c\ascii-control\pokemon-y\0004000000055E00\romfs\a\0\7\4` as the source and the Y target path. This tests each Title ID independently.

Only after the ASCII result is visible, replace X and Y one at a time with the corresponding `build\milestone-2c\russian\pokemon-x\0004000000055D00\romfs\a\0\7\4` or `build\milestone-2c\russian\pokemon-y\0004000000055E00\romfs\a\0\7\4` file. Reopen the game and record whether `Привет!` appears correctly, as missing-glyph boxes, or with another fallback. Capture screenshots and the current AzaharPlus log for each run. The ASCII control isolates resource loading from Cyrillic rendering.

Restore the Milestone 2B files by closing AzaharPlus and copying the saved `pokemon-x-a074` and `pokemon-y-a074` backups back to their original target paths. Alternatively remove only the exact `a\0\7\4` file if you intend to disable this project's probe and have confirmed it belongs to this project. Preserve other mods, saves, installed updates, and original game files.

## Logs and interpretation

The inspected `%APPDATA%\AzaharPlus\log\azahar_log.old.txt` records launches of base Title IDs `0004000000055D00` and `0004000000055E00`, but contains no LayeredFS or `load\mods` entries. The current `azahar_log.txt` was empty at inspection. The installed `a/0/7/4` files matched the earlier generated Milestone 2B outputs by SHA-256, but their in-game result was inconclusive because message 35/0 ID 22 is not the screenshot label.

Seeing `ASCII 2C` in the next run will be direct runtime evidence that the new update archive resource is overlaid. If the exact ASCII label remains visible even though it is present in the update-only member, that separates the problem from glyph support and points to the effective mod path, competing mod, update resource selection, or runtime cache. Record the title ID and update version shown by the emulator, screenshot, mod file hash, and complete log before reporting.

After LayeredFS is confirmed, test uppercase and lowercase Cyrillic, Ё/ё, punctuation, mixed digits, and a longer wrapped string before starting bulk translation. Verify other menus and gameplay screens in later QA. No Milestone 2C variant has been installed or launched by this project run.
