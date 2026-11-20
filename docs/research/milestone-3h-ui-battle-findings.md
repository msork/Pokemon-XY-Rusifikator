# Milestone 3H UI and Battle Localization Findings

Date: 2026-11-20

## Runtime evidence supplied by the owner

The latest screenshots document these observations in Pokémon X:

- The PC line is now legible and retains the requested neutral form `проверил(а)`.
- The mirror line `...И ты уже без пижамы!` is legible.
- A nickname-choice screen still shows the choices `Li’l B`, `Lady B`, `B-kins`, and `Pick your own`; its preceding line is Russian.
- The name-entry prompt is `Your nickname?`, and the displayed keyboard is Latin-only.
- Starter selection shows `Чеспин`, while `Fennekin` and `Froakie` remain English.
- A battle screenshot shows an opposing species field as question marks, while the Fennekin label is English. It also shows English action labels and move/type names, plus `HP`; the move PP abbreviation is `ОС`.
- The bag screenshot shows English categories. The Prof’s Letter acquisition line remains English.

These owner screenshots are runtime evidence for Pokémon X only. They are not evidence for Pokémon Y or for any new Milestone 3H text candidates.

## Verified message resources

Source IDs use `resource:member/message`. The following candidates were extracted from the English message corpus and included in `translations/milestone3h-ui-battle.jsonl` as drafts. Their text/control segments and source hashes are retained by record ID.

| Purpose | Resource ID | Finding |
|---|---|---|
| Name prompt (`Your name?`) | `a/0/7/4:0036/00:00000` | TextFile string |
| Nickname fragment (`’s nickname?`) | `a/0/7/4:0036/00:00001` | A fragment; punctuation/spacing depends on its caller |
| Nickname prompt | `a/0/7/4:0036/00:00004` | TextFile string matching the screenshot |
| Delete/OK/Space | `a/0/7/4:0036/00:00013–00016` | TextFile labels; the screen’s key captions are separately rendered |
| Nickname options | `a/0/7/4:0079/00:00000–00008` | Mixed text/control fragments; options are assembled with variables and special control events |
| Species names | `a/0/7/4:0080/00:00650`, `00653`, `00656` | Chespin, Fennekin, Froakie. Existing species glossary resolves to Чеспин, Феннекин, Фроки respectively. The screenshot confirms only Чеспин on the starter screen. |
| Prof’s Letter item name | `a/0/7/4:0096/00:00642` | Singular item-name candidate |
| Bag category labels | `a/0/7/4:0127/00:00035–00036`, `00040–00041`, `00043–00045` | TextFile strings for restore categories, Poké Balls, battle items, and last-used item |
| Move names | `a/0/7/4:0013/00:{00010,00033,00039,00052}` and `0014/00:{00010,00033,00039,00052}` | TextFile candidates for Scratch, Tackle, Tail Whip, and Ember; runtime binding still needs checking |
| Type names | `a/0/7/4:0017/00:{00000,00009,00010,00011}` | Normal, Fire, Water, Grass text candidates; battle-screen binding not confirmed |
| Trainer challenge / faint messages | `a/0/7/4:0124/00:00008`, `0125/00:00000–00002` | TextFile templates with dynamic trainer/species variables |
| Move-use messages | `a/0/7/4:0126/00:00030–00032`, `00099–00101`, `00117–00119`, `00156–00158` | TextFile templates with species variables and literal move names |
| Prof’s Letter acquisition | `a/0/8/2:0142/00:00001` | Exact script record; contains player-name variable, line break, color controls, and item-name placeholder. Every control word remains in the draft. |
| Nickname discussion/confirmation | `a/0/8/2:0049/00:00013–00023`, `00034–00036` | Script message candidates for the nickname proposal and Pokémon nickname confirmation sequence |

The generator considers 82 candidate records; 27 were already present in the pilot, early-game, or Milestone 3G files and are omitted to prevent duplicate IDs. The resulting 55 new records in the Milestone 3H JSONL are `draft`, pending linguistic and runtime review. The new records do not change the prior PC/mirror records in `translations/early-game.jsonl`.

## Effective resource versions

X and Y resources in the local extracted datasets are byte-identical for the files checked. Hashes are identical between X and Y:

- `a/0/7/4` base: `18c12ccb9baf48c9a33e46b77b372c3124a64ad84dae0c03ee50229650a26760`.
- `a/0/7/4` update 1.5: `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881`. Update copy is effective.
- `a/0/8/2` base: `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999`; no update 1.5 copy exists in the extracted update datasets.
- `a/0/1/9` base: `30b0849ed6013b922551cb6e8b7913b992cd8c0aff7cfa9451f06060d1f4cc97`; no update override found.
- `a/2/4/0` base: `5d5fce79754723726bd18271aeaed844c9c9a95f088076ad48de5cf66b22ecbb`; no update override found.

The update precedence here follows the verified local file presence and the earlier owner-confirmed LayeredFS test with update 1.5 enabled. No new patch was built or installed in this milestone.

## Why Chespin can be correct at selection but unknown in battle

The name-table string `Chespin` is `a/0/7/4:0080/00:00650` and its Russian species glossary mapping is `Чеспин`. The owner screenshot confirms this mapping is rendered in the starter selection interface. The battle screenshot’s opposing name field consists of question marks and includes a female symbol and level, while the chosen Fennekin’s battle name is English. This does not establish that the question-mark field is Chespin: it can reflect an unidentified opponent or a distinct dynamic name source.

No static evidence in the RomFS-only dump identifies the battle’s question-mark name source or establishes a missing Cyrillic font mapping. The actual ExeFS/code is not in this workspace. The Russian starter-screen success also shows that general Cyrillic display is available in at least that screen, but does not establish that every battle label uses the same path/font. Root cause remains unresolved.

Next owner check: after a species is registered/identified, compare that same Pokémon’s name in the Pokédex or party and in a battle HUD. Also compare the chosen starter’s own HUD in battle with its starter-selection label. Record exact X/Y game, species, opponent/player role, and whether the name changes after identification.

## Text-entry keyboard and Cyrillic input

`a/0/1/9` is present in base X and Y and has GARC entries `0/0`, `1/0`, `1/2`, `1/3`, `1/4`, `1/5`, `1/7`, and `1/8`. The resource’s layouts reference `namebar_lower.bclyt`, `namechange_lower.bclyt`, `nameinput1_lower.bclyt`, `nameinput2_lower.bclyt`, and `nameinput_upper.bclyt`; texture references include `base.bclim`, `button01.bclim`, `button02.bclim`, `mode03.bclim`, and `strinput_bg.bclim`. The embedded font reference is `cbf_std_kujira.bcfnt`.

The screenshot and resource names support that these layouts provide name-entry graphics. They do not expose the key-to-character input table or prove that replacing key images changes the character emitted by a key press. The key labels are dynamically rendered rather than baked into the exported button graphics. RomFS alone does not include the executable/input handling code needed to map a Cyrillic key selection to a Cyrillic character.

A correct Cyrillic keyboard design needs both sides of the mapping: (1) visible Cyrillic upper/lower key labels, Ё/ё, punctuation and page controls, and (2) input values that emit the matching game character codes, with working space, delete, cursor, and accept behavior. Replacing Latin key artwork alone would be misleading and is not proposed. The embedded `cbf_std_kujira.bcfnt` cmap has not been independently decoded here; do not assume Cyrillic glyph support for that keyboard font based on the language-selection screen.

## Battle images and manual editing

`a/2/4/0` member `0/2` is the English UI texture set. Its BCLIM resources visibly contain the command labels on button art and HP/Lv. labels baked into gauge art. `a/2/3/9` member `0/2` contains the English type-label BCLIMs; direct PNG inspection confirmed `type_icon_00_normal.bclim` reads `NORMAL` and `type_icon_09_honoo.bclim` reads `FIRE`, matching the owner's battle screenshot. The required PNGs were generated for inspection only under ignored `build/milestone-3h/texture-editing/`.

The command/HUD image paths use this prefix, with separate `pokemon-x/0004000000055D00` and `pokemon-y/0004000000055E00` directories:

`a_2_4_0/member-0000-02/`

- `fight_text.bclim.png` — 80×50; text `FIGHT`.
- `bag_button.bclim.png` — 128×64; text `BAG`.
- `pokemon_button.bclim.png` — 128×64; text `POKÉMON`.
- `run_button.bclim.png` — 110×55; text `RUN`.
- `ally_gauge.bclim.png` — 128×32; baked `HP` and `Lv.` labels.
- `enemy_gauge.bclim.png` — 128×32; baked `HP` and `Lv.` labels.
- `move_button.bclim.png` — 80×40; background/button element, no confirmed English label. Keep only if layout inspection requires it.

Each PNG manifest row records its original internal filename, dimensions, BCLIM format, original archive hash, original BCLIM SHA-256, and output PNG SHA-256. The BCLIM member has archive/member identity `a/2/4/0:0000/02`; original filename is preserved in the PNG suffix. These are extracted previews, not replacements. No reinsertion code or tested replacement was produced.

**Images requiring owner edit:** the six images above containing text (`fight_text`, `bag_button`, `pokemon_button`, `run_button`, `ally_gauge`, `enemy_gauge`). The `move_button` image is optional and has no confirmed label. Keep original dimensions and transparency; preserve game art and replace only letters. For the gauge art, replace `HP` with `ОЗ`; retain `Lv.` unless a separate Russian level abbreviation is approved. Do not edit text labels in unrelated locales.

The type-label image path prefix is `a_2_3_9/member-0000-02/`. All 18 50×20 type labels are separately named, and all are in the English member. The source archive member ID is `a/2/3/9:0000/02`. The `source_bclim_sha256` for each entry is in the generated manifest; the image names are:

`type_icon_00_normal.bclim.png`, `type_icon_01_kakutou.bclim.png`, `type_icon_02_hikou.bclim.png`, `type_icon_03_doku.bclim.png`, `type_icon_04_jimen.bclim.png`, `type_icon_05_iwa.bclim.png`, `type_icon_06_mushi.bclim.png`, `type_icon_07_ghost.bclim.png`, `type_icon_08_hagane.bclim.png`, `type_icon_09_honoo.bclim.png`, `type_icon_10_mizu.bclim.png`, `type_icon_11_kusa.bclim.png`, `type_icon_12_denki.bclim.png`, `type_icon_13_esper.bclim.png`, `type_icon_14_koori.bclim.png`, `type_icon_15_dragon.bclim.png`, `type_icon_16_aku.bclim.png`, and `type_icon_17_yousei.bclim.png`.

**Images requiring owner edit:** the six command/HUD images listed above and the 18 type-label images. Each has separate X and Y preview copies with identical source hashes. Preserve original dimensions, transparency, color treatment, and embedded visual style; only replace lettering. The battle screenshot verifies `NORMAL` and `FIRE`; do not treat the other icon labels as owner runtime-tested. `move_button.bclim` is optional and contains no confirmed label.

An image-edit/rebuild milestone must implement and test PNG-to-BCLIM for the exact original formats, update the internal resource pack deterministically, and rebuild the enclosing archive. The current extractor does not provide safe reinsertion, so edited images must not be installed yet.

The name-entry resources also contain 13 BCLIMs in member `0/0` with format 11 (`ETC1A4`). Current project PNG export supports formats 7–9 only. This is why the keyboard-background PNGs are recorded as unsupported in the ignored extraction manifest, rather than emitted with corrupted pixels. These are graphics/backgrounds, not the dynamic keyboard labels. A compatible ETC1A4 decoder is needed before they can be offered as editable PNGs.

The English `FIGHT`/`BAG`/`POKÉMON`/`RUN` labels, `HP`/`Lv.` gauge lettering, and move-type tags such as `NORMAL`/`FIRE` are image content in these resource sets, not message-table strings. Bag category descriptions, move names, species names and battle prose are text-table candidates listed above. The screenshot does not by itself prove which text-table move/species record is bound to every battle screen.

## Abbreviations and unresolved text

The new bag and battle text drafts use Cyrillic `ОЗ` for HP and `ОС` for PP. These drafts do not alter numeric values or controls. A code review/test asserts Cyrillic forms rather than Latin `OZ`/`OS`. The gauge screenshot’s `HP` is baked into the two gauge images and cannot be fixed through TextFile replacement alone.

Fennekin and Froakie have verified species-table entries and glossary mappings (`Феннекин`, `Фроки`), included as drafts. A screenshot confirms they remain English during starter selection, so the tested patch state has not yet applied those candidates. The English acquisition line maps to `a/0/8/2:0142/00:00001`; its item name has an `a/0/7/4:0096/00:00642` candidate. Both preserve their variables/control events, but neither has new runtime validation.

## Tests and boundaries

Automated tests cover source hashes/control-event parity for the 82 generated drafts, expected screenshot anchor records, glossary-backed starter names, preservation of the PC/mirror lines, X/Y equality, and explicit rejection of unsupported ETC1A4 by the current PNG decoder. Tests do not emulate the game, prove runtime text-to-screen binding, decode executable logic, or validate image reinsertion.

No originals, saves, installed mods or emulator settings were changed. No new patch was generated or installed. No AzaharPlus launch was performed by the development agent.

## Technical references

- pk3DS BCLIM reader (format behavior, not copied into project code): https://github.com/kwsch/pk3DS/blob/master/pk3DS.Core/CTR/Images/BCLIM.cs
- Gen VI-and-later character encoding reference: https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_V%E2%80%93present)

The pk3DS BCLIM implementation is GPL-3.0. The project only used it as a format reference; no code was copied. This document and original scripts remain under project WTFPL terms; game-derived assets and the separately licensed species-name dataset retain their own restrictions.

### Editable image manifest details

| Resource/member | Original internal filename | Dimensions | Source BCLIM SHA-256 |
|---|---|---:|---|
| `a/2/3/9:0/2` | `type_icon_00_normal.bclim` | 50?20 | `b563e36b3a9e43f4bc87a23745069c6155f906b16922d08a0defb3a4c6198a3b` |
| `a/2/3/9:0/2` | `type_icon_01_kakutou.bclim` | 50?20 | `f3336432fe52c698964e21d52641446ee043991b2194235ac4e08b85d1a7a7a0` |
| `a/2/3/9:0/2` | `type_icon_02_hikou.bclim` | 50?20 | `693318696ff8c8f5e9ae62022a06abf31408093b1d5e492cea1e1e8d4a1f8a8e` |
| `a/2/3/9:0/2` | `type_icon_03_doku.bclim` | 50?20 | `382ec52a5e0d154fabf7c731f9e6fa7eab9c37f2988bd36466cfbc5b52faad02` |
| `a/2/3/9:0/2` | `type_icon_04_jimen.bclim` | 50?20 | `f128d45d3cdc2fb34df22da93bba8ff5e0da3d6da81e19417d97aba8cecd0630` |
| `a/2/3/9:0/2` | `type_icon_05_iwa.bclim` | 50?20 | `cd876661d14c783cac355a0096d83c5db001f09ddd29c474159cc6e021c6241f` |
| `a/2/3/9:0/2` | `type_icon_06_mushi.bclim` | 50?20 | `5f724b3561f8bcc0c9fe378f21ec52314c94d91d9435def8cace3308ac1eac60` |
| `a/2/3/9:0/2` | `type_icon_07_ghost.bclim` | 50?20 | `e5f22b2a13330c7919f0775449e435465e710c248245844e8cc328870cffdad8` |
| `a/2/3/9:0/2` | `type_icon_08_hagane.bclim` | 50?20 | `f8f915f3bd6805be9b22a6e64a0271c23ca6af9a9139b73683a15dd3c61cdd40` |
| `a/2/3/9:0/2` | `type_icon_09_honoo.bclim` | 50?20 | `c64a682b74c6bdc36b025f456b177275dccd1d5a8bb4640132bf4961a2086e89` |
| `a/2/3/9:0/2` | `type_icon_10_mizu.bclim` | 50?20 | `322161751688b3fbca6bb40df812a8118ccfb3f01ade4174dc6d4eefb092d17a` |
| `a/2/3/9:0/2` | `type_icon_11_kusa.bclim` | 50?20 | `f842d0b0f2b2710a14a4024900e12c2e9d92b8f7e143ea488e7a3905868e3e88` |
| `a/2/3/9:0/2` | `type_icon_12_denki.bclim` | 50?20 | `c5b5073f5b5252941fca2aa43641e49bf23fc74e9838aed0c99cbd045f80d136` |
| `a/2/3/9:0/2` | `type_icon_13_esper.bclim` | 50?20 | `200433f372a06b25c89493710189748e1868b379251ec7bdb333874d2c778b7e` |
| `a/2/3/9:0/2` | `type_icon_14_koori.bclim` | 50?20 | `230f7eee151cb1c7a67b06c84c85cdc4af0a2276523ea33739fd4fbf6f3a8117` |
| `a/2/3/9:0/2` | `type_icon_15_dragon.bclim` | 50?20 | `790b488c5e45a5e8e82e9cc1670cd5f6683a878f9bc3c0592c75ebeb6305f55f` |
| `a/2/3/9:0/2` | `type_icon_16_aku.bclim` | 50?20 | `a36f904e8d2e640ec148c019991d048b40670577fc8100a6a2a8342076c4b8f7` |
| `a/2/3/9:0/2` | `type_icon_17_yousei.bclim` | 50?20 | `72f44b2e4f10bce4dbfe086f7f6bb4bc3d838512c3675d6c2146d8d09fbddb6a` |
| `a/2/4/0:0/2` | `ally_gauge.bclim` | 128?32 | `581c2de153b1f373e1f079be96f5407b7c4b114e0ce59d856daa484a6920b0ea` |
| `a/2/4/0:0/2` | `bag_button.bclim` | 128?64 | `d035a3cbebc3543208dad575341b04a30055f87d55a66976defdb6f56892654a` |
| `a/2/4/0:0/2` | `enemy_gauge.bclim` | 128?32 | `3a70a95336271cb71bc35382248cf71b2a343f7a7e9ae1e3bed4a9266fe606bf` |
| `a/2/4/0:0/2` | `fight_text.bclim` | 80?50 | `f716c42139ad8b197f1bd2f4a68f768b4b44d8478fc1407d16dd432bbeff3f9d` |
| `a/2/4/0:0/2` | `move_button.bclim` | 80?40 | `82fff5bd832eecf2352d2e93753d2a7dc34f8e57782975705712a2edcb446b24` |
| `a/2/4/0:0/2` | `pokemon_button.bclim` | 128?64 | `4cccecea33f316d9a6d4d4b24fef766b476ccc247b0e4acd692ddb8faf06a852` |
| `a/2/4/0:0/2` | `run_button.bclim` | 110?55 | `f525715f37ce592b9613f39bc6ef79d4d1e4aafaa3979a1267b45a919293bbf6` |
