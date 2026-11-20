# Milestone 3G owner runtime checklist

The candidate is installed in both LayeredFS mod folders but has **not** been launched for Milestone 3G runtime evaluation. All rows remain drafts, not final linguistic approval. Do not overwrite a save. Run Pokémon X and Pokémon Y separately with update 1.5 enabled.

## Candidate archives

| Game | Candidate source | LayeredFS target |
|---|---|---|
| Pokémon X (`0004000000055D00`) | `build/milestone-3g/candidate/pokemon-x/romfs/a/0/7/4` | `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4` |
| Pokémon X (`0004000000055D00`) | `build/milestone-3g/candidate/pokemon-x/romfs/a/0/8/2` | `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\8\2` |
| Pokémon Y (`0004000000055E00`) | `build/milestone-3g/candidate/pokemon-y/romfs/a/0/7/4` | `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4` |
| Pokémon Y (`0004000000055E00`) | `build/milestone-3g/candidate/pokemon-y/romfs/a/0/8/2` | `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\8\2` |

The installer backed up all four existing Milestone 3F target files before replacement. Their original and installed hashes are recorded in [the deployment record](milestone-3g-deployment.md) and ignored `build/milestone-3g/installation-record.json`.

## Scene-ordered checks

Perform every applicable check in both games. Start from a test save that can be restored without overwriting the owner's save. Note protagonist gender and game for every observation.

| Order | In-game place/action | Candidate data | Expected observation | Scene evidence |
|---|---|---|---|---|
| 1 | Vaniville Town bedroom: interact with the PC | `a/0/8/2`, member `0055/00`, message `00001` | The line begins with the player name followed by a space and `проверил(а)`; it contains no duplicated `Ты`, and reads `...компьютер, который папа подарил тебе.` Later Adventure Rule pages remain present. | The owner already reported the defective PC text in Pokémon X with the female protagonist. The scene mapping is therefore owner-observed for that test; X male and both Y variants still need checking. |
| 2 | Same bedroom: interact with the mirror | `a/0/8/2`, member `0055/00`, message `00003` | `…И ты уже без пижамы!` appears without a stray Latin or Cyrillic character. | The owner reported the defective mirror text during X female testing. X male and both Y variants still need checking. |
| 3 | Open the field menu | `a/0/7/4`, member `0114/00`, messages `00000–00005` | Check the Pokémon, Pokédex, Bag, Save, and Options labels. The existing pilot already translates some menu records; compare the rendered labels with the exact IDs in the candidate. | Text values are verified in the English TextFile. Their precise on-screen placement is inferred from the labels; capture what the game actually shows. |
| 4 | Open the party summary and move view | `a/0/7/4`, members `0011/00`, `0012/00`, `0064/00`, `0127/00`, `0129/00`, `0140/00` | Check `ОЗ`, `ОС`, `Ур.` and `ДО СЛ. УР.`. Verify all numeric values and bar positions are unchanged and the labels fit without overlap. | The abbreviations and label strings are verified in TextFile records. Exact screen bindings are inferred and require screenshots. |
| 5 | Start a battle, then open command and move selection screens | `a/0/7/4`, members `0114/00`, `0127/00`, `0129/00`; battle text members `0124/00–0126/00` | Record FIGHT, BAG, RUN, POKÉMON, HP, PP, level text, Pokémon names, and each battle message actually seen. The FIGHT source remains unresolved and may stay English in this candidate. | The owner previously reported English battle UI and battle text, but those observations were not tied to exact message IDs. Matching TextFile strings exist for some labels; the FIGHT label was not found in the TextFile catalog. |
| 6 | View Chespin in a party/Pokédex context, if available in the test save | `a/0/7/4`, member `0080/00`, message `00650` | The species name should use `Чеспин`, matching National Pokédex #650. | The source string and glossary lookup are verified. The screen where the game consumes this specific record is inferred until observed. |

## Report back

For each title, report the protagonist gender, whether each line appeared, visible spelling, missing/extra symbols, wrapping/overlap, and whether numbers remained unchanged. Capture screenshots of both bedroom lines, the party/move screens, and one battle. Separately state whether FIGHT remains English; that result will guide the texture or executable investigation. Do not mark any draft as reviewed or tested until the observation is recorded against its message ID.
