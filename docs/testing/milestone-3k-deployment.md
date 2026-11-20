# Milestone 3K Deployment and Owner Test Plan

## Text candidate installed

The installed text build is the Milestone 3J integrated candidate of 227 unique records (12 machine drafts and 215 drafts). These are runtime-test drafts and are not final linguistic approval. The installer wrote only the following four LayeredFS targets in the verified AzaharPlus 2126.2-A mod root `%APPDATA%\AzaharPlus\load\mods`:

| Game / base Title ID | Resource | Effective source | Installed SHA-256 |
| --- | --- | --- | --- |
| X / `0004000000055D00` | `a/0/7/4` | Update 1.5 | `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e` |
| X / `0004000000055D00` | `a/0/8/2` | Base fallback | `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` |
| Y / `0004000000055E00` | `a/0/7/4` | Update 1.5 | `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e` |
| Y / `0004000000055E00` | `a/0/8/2` | Base fallback | `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` |

PokÃ©mon X and PokÃ©mon Y were built and installed separately. In the extracted datasets, update 1.5 contains `a/0/7/4` and overrides its base copy. Update 1.5 does not contain `a/0/8/2`, so the base archive is effective. GARC identity rebuilds, source hashes, message control/placeholder sequences, translated message words, and untranslated content were checked during construction. For each archive, all unrelated GARC members were byte-identical: 120 in `a/0/7/4` and 419 in `a/0/8/2`.

The exact current mod root and installed hashes were read back. No emulator was launched, no save was read or written, and no source or update data was changed. All four targets existed before installation and matched the previous Milestone 3G install hashes. Their exact backups are in ignored `build/milestone-3k/installation-backups/20261120T230822Z/manifest.json` and the corresponding four files. The previous Milestone 3G install and backup records remain under `build/milestone-3g/` and were not replaced.

## Text rollback

Close AzaharPlus before restoring files. From the repository root, run:

```powershell
python scripts/install_milestone3k_text.py --rollback
```

Rollback first checks that all four installed targets still have the recorded 3K hashes and that all four Milestone 3K backup hashes match. It then restores the exact pre-3K files (the Milestone 3G files) and verifies their hashes. If any installed target has changed, it refuses before restoring any file. To continue further back to the pre-3G state, run the existing Milestone 3G rollback only after this 3K rollback succeeds:

```powershell
python scripts/install_milestone3g.py --rollback
```

This reverse order preserves the earlier rollback chain. The Milestone 3G installation and backup records are retained.

## Rejected Russian FIGHT artwork draft

The canonical 24-PNG workspace remains unchanged. Its original `fight_text.bclim.png` SHA-256 is `c3317a191a48b540b0e3b87e35baed574d4d47f0bf4171c5beeb0d95280646b9`. The earlier generated Russian label draft failed owner review for poor letterforms, alignment, and styling. Do not use or reinstall that draft.

The two image targets were rolled back on 2026-11-20. Both were absent before the test, and both are absent again. The rollback record is `build/milestone-3k/image-install/rollback-record.json`; its backup and installation records remain as audit history. The four text targets were rechecked and still match their Milestone 3K hashes. The rejected image PNG/archive candidates and their generation/installation scripts were removed. No replacement lettering was generated.

## Owner runtime checklist

Test each game separately with AzaharPlus 2126.2-A and update 1.5 enabled. The Russian battle image is currently rolled back, so the FIGHT button should remain original English artwork during this test.

1. Launch Pokemon X and confirm the title/language-selection and opening flow.
2. Follow the opening and early-game sequence. Check localized character selection, mother, neighbors, Vaniville Town, Aquacorde Town, Shauna/Calem or Serena, starter selection, and early battles where the candidate has records.
3. In the first battle, record the original FIGHT image and the translated text/interface independently. Check BAG/RUN/POKEMON, species and move names, HP/PP terms, level labels, and battle messages as present.
4. Check variable substitutions and punctuation, including the gender-neutral PC line `проверил(а)` and mirror line.
5. Record exact scene, game, version, screenshots, and visible text. Drafts remain unapproved.
6. Repeat independently in Pokemon Y. X results do not establish Y behavior.
