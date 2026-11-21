# Milestone 3L Manual FIGHT Texture Installation

## Installation record

Only the `a/2/4/0` image archive was installed, separately for the two base-game Title IDs. The unchanged `a/2/3/9` type-label archive was not installed.

| Game | Title ID | LayeredFS resource | Installed SHA-256 |
| --- | --- | --- | --- |
| Pokemon X | `0004000000055D00` | `a/2/4/0` | `1becfbb516f81ce2f885490b9dfba6b2404524b7b1cf87e0669cdba56f58fc0e` |
| Pokemon Y | `0004000000055E00` | `a/2/4/0` | `1becfbb516f81ce2f885490b9dfba6b2404524b7b1cf87e0669cdba56f58fc0e` |

Both targets were absent before this installation. Their original existence states and backup hashes are recorded in `build/milestone-3l/image-install/installation-backups/20261121T052710Z/manifest.json`. The install record is `build/milestone-3l/image-install/installation-record.json`.

The installer validated both candidate files against the Milestone 3I manifest and the expected hash before copying. It verified each installed file by reading it back. It also checked all four Milestone 3K text archives before and after image installation; their hashes remain unchanged. No saves, game/update assets, or unrelated mods were changed. AzaharPlus was not launched. The image is not runtime-tested.

## Image-only rollback

Close AzaharPlus before rollback. Run from the repository root:

```powershell
python scripts/install_milestone3l_image.py --rollback
```

Rollback verifies both current image hashes and the recorded backup manifest before changing anything. Since both `a/2/4/0` targets were originally absent, it removes only those two image files. The four text archives and every other mod remain untouched. The rollback record will be written to `build/milestone-3l/image-install/rollback-record.json`.

## Owner runtime check

After deciding when to launch the games, test X and Y independently with AzaharPlus 2126.2-A and update 1.5 enabled. Reach the first battle's lower-screen command menu and record whether the manually edited Russian FIGHT label is legible, centered, and visually consistent at normal display size. Capture the game/version and screen for each title. No runtime success is claimed until owner results are reported.
