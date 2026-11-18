# AzaharPlus 2126.2-A Test Plan

## Target profile

- Windows installation: `C:\Users\maxim\Games\azaharplus-2126.2-A-windows`
- Observed user data: `%APPDATA%\AzaharPlus`
- Expected per-game mod roots: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs` (X) and `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs` (Y)
- Both games must have update 1.5 enabled. Keep update Title IDs out of the LayeredFS folder name unless a target-build test proves otherwise.

The user-data path and existing LayeredFS use are locally observed for this AzaharPlus installation. Exact update-precedence and mod replacement behavior for Pokémon X/Y have not been verified. The paths above are expected test locations, not a claim of a completed game test.

## Required runtime evidence

Before translation work, launch each game with its update active and capture the version shown by AzaharPlus, title ID, log entry confirming the LayeredFS replacement, and the in-game screen. Test uppercase/lowercase Cyrillic, Ё/ё, punctuation, mixed digits, and a string long enough to wrap. Verify title/menu, dialogue, battle, item, summary, Pokédex, settings, and save loading in later QA. Preserve saves and do not alter installed updates or original `.3ds` files.

To establish update resolution, use a test-only replacement for a harmless candidate resource and compare the runtime result with the base and update member fingerprints. Remove only the test mod after recording results. Do not report success until evidence is recorded here.
