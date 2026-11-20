# Milestone 3K Deployment and Owner Test Plan

## Text candidate installed

The installed text build is the Milestone 3J integrated candidate of 227 unique records (12 machine drafts and 215 drafts). These are runtime-test drafts and are not final linguistic approval. The installer wrote only the following four LayeredFS targets in the verified AzaharPlus 2126.2-A mod root `%APPDATA%\AzaharPlus\load\mods`:

| Game / base Title ID | Resource | Effective source | Installed SHA-256 |
| --- | --- | --- | --- |
| X / `0004000000055D00` | `a/0/7/4` | Update 1.5 | `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e` |
| X / `0004000000055D00` | `a/0/8/2` | Base fallback | `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` |
| Y / `0004000000055E00` | `a/0/7/4` | Update 1.5 | `35e917bafa9016d119288bc263a57b2975b6dfd932e2f5d188cd334d65ebd53e` |
| Y / `0004000000055E00` | `a/0/8/2` | Base fallback | `3be4d01de1837190a959c2782a0a4bbd7e6192632eba12d5eb9c4a1f250d5d99` |

Pokémon X and Pokémon Y were built and installed separately. In the extracted datasets, update 1.5 contains `a/0/7/4` and overrides its base copy. Update 1.5 does not contain `a/0/8/2`, so the base archive is effective. GARC identity rebuilds, source hashes, message control/placeholder sequences, translated message words, and untranslated content were checked during construction. For each archive, all unrelated GARC members were byte-identical: 120 in `a/0/7/4` and 419 in `a/0/8/2`.

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

## Separate Russian FIGHT artwork test

The canonical 24-PNG owner set remains unchanged; its `fight_text.bclim.png` hash remains `c3317a191a48b540b0e3b87e35baed574d4d47f0bf4171c5beeb0d95280646b9`. The separate disposable label PNG is `build/milestone-3k/fight-artwork-test/fight_text.bclim.png`, at the original 80 × 50 RGBA dimensions, and contains the test label `БОЙ`. Its SHA-256 is `fefe7e48d9ecb4a442766d07a5bbcb6e545e6ffd3bb9a26f643a43be612b3f95`.

The candidate consists only of the `a/2/4/0` GARC archive for each base Title ID. Both use the base resource. The builder replaces only `0/2` → `fight_text.bclim`, retaining the other 10 textures and 6 of 7 GARC members byte-for-byte. The internal pack round trip passed. Format 8 is RGBA4444; maximum source-PNG to decoded-BCLIM channel delta is 0 for this test. Candidate SHA-256:

| Game / base Title ID | Candidate resource | SHA-256 |
| --- | --- | --- |
| X / `0004000000055D00` | `a/2/4/0` | `49331e59b6bdcf687d1387d5eae9f8760822177333634743e611cf2aba15d3f3` |
| Y / `0004000000055E00` | `a/2/4/0` | `49331e59b6bdcf687d1387d5eae9f8760822177333634743e611cf2aba15d3f3` |

The image test is **not installed**. If a later owner request authorizes its runtime test, first verify `build/milestone-3k/image-candidate/manifest.json`, then run:

```powershell
python scripts/install_milestone3k_image_test.py --install
```

This separate installer backs up only the two X/Y `a/2/4/0` mod targets under `build/milestone-3k/image-install/`, records originally absent targets, and verifies installed hashes. It does not touch the four text targets. Roll back just the image test with:

```powershell
python scripts/install_milestone3k_image_test.py --rollback
```

The image rollback preflights the installed hashes and backups before changing targets. Its record and backup directory are separate from the text installer and Milestone 3G records.

## Owner runtime checklist

Test each game separately with AzaharPlus 2126.2-A and update 1.5 enabled. No new runtime behavior is claimed until the owner reports results.

1. Launch Pokémon X and confirm the game reaches the title/language selection and opening flow without a blank panel or crash.
2. Follow the opening and early-game sequence. Check the localized character selection, mother, neighbors, Vaniville Town, Aquacorde Town, Shauna/Calem or Serena branch, starter selection, and early battles where the candidate has records.
3. In the first battle, check translated FIGHT/BAG/RUN/POKÉMON UI text, species and move names, ОЗ/ОС terms, level labels, and battle messages. Some of these labels remain separate image work and will still be English until the image candidate is separately installed.
4. Check variable substitutions and punctuation, including the player name and gender-neutral `проверил(а)` PC line, plus the mirror line.
5. Record exact displayed text, scene, game version, and screenshots. Do not mark draft records approved based only on this smoke test.
6. Repeat independently in Pokémon Y. X results do not establish Y behavior.

The battle image test requires a separate installation request. It is intentionally excluded from the current mods so text and artwork can be evaluated independently.
