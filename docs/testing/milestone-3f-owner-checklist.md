# Milestone 3F Owner Runtime Checklist

The expanded patch is installed under the base-game Title IDs in AzaharPlus 2126.2-A. Run Pokémon X and Y separately with update 1.5 enabled. Every Milestone 3E string is still draft content. Do not treat an earlier scene check as a test of the current expanded archive.

## Previously tested versus new

- **Previously owner-tested in Milestone 3C:** Pokémon X with a female protagonist showed the earlier pilot's Options, mother's dialogue, Calem, and Shauna content. The pilot records associated with those contexts were `a/0/7/4` member `75/0` messages `0, 3–7`; `a/0/8/2` member `55/0` messages `10, 13`; and member `57/0` messages `1, 2, 3, 6`. The earlier checklist says exact scene triggers were inferred, so this is scene-level evidence rather than proof of each individual line. The Options explanation and several draft translations changed in 3E; re-check these screens.
- **Untested after Milestone 3E installation:** all four installed archives and all expanded content, including the home-PC/mirror lines, remaining Vaniville dialogue, protagonist branches, Aquacorde, starter menu, battle messages, and move strings. Pokémon Y, male-protagonist scenes, Serena, and the gender-controlled substitutions remain unverified.

## Test order

For gameplay scenes, use a disposable new-game/test-save environment. Do not overwrite a normal save. If only the existing save is available, stop before entering or saving into gameplay; the initial language screen can be checked without confirming a language.

1. **Options / update 1.5 UI** — In each game, inspect Options > Text Speed: `a/0/7/4`, member `75/0`, messages `0`, `3–7`. Confirm labels, meanings, Cyrillic, line fit, and wrapping. The current message 7 draft differs from the previously tested pilot wording.
2. **Home / variables and gender controls** — Check `a/0/8/2`, member `55/0`, messages `0–3` and `10–28`. Prioritize message `1` (PC/player variables), `3` (gender-coded pajama line), `10` (player-name variable), `22` (name/Pokémon substitutions), `26` (boy/girl control), and `27` (button/menu tutorial). Record whether any control emits untranslated or malformed text.
3. **Neighbors / protagonist branches** — Check member `57/0`, messages `1–13`, plus `a/0/8/2` member `53/0`, messages `0–3`. Use male and female protagonists in separate disposable runs. Verify Serena/Calem selection, pronoun agreement, and whether the intended branch appears. Branch mapping for member `53/0`, messages `2–3`, is inferred.
4. **Aquacorde Town** — Check member `49/0`, messages `0–59`, then sign/location message `70`. Pay attention to name variables, nickname prompts, starter handoff, Pokédex handoff, and the first rival battle. Confirm dialogue continues through each clear/page event.
5. **Starter-selection menu** — Check `a/0/7/4`, member `63/0`, messages `0–5`. Confirm all three type labels, selection prompt, chosen-Pokémon substitution, and layout.
6. **Battle UI and text** — Check `a/0/7/4`, members `124/0` messages `71–72`; `125/0` messages `0–2`; and `126/0` messages `3–5`, `30–32`, `66–68`, `99–101`, `117–119`, `135–137`. Some are conditional templates and may not appear in every first battle. Record every visible one, substitutions, text timing, and clipping.

## Record separately for each game and protagonist

- [ ] Pokémon X, male protagonist
- [ ] Pokémon X, female protagonist
- [ ] Pokémon Y, male protagonist
- [ ] Pokémon Y, female protagonist

For each run, note scene/message IDs actually observed, whether intended English source was replaced, exact visible Russian, variable values, line/page transitions, overflow, and gameplay continuation. Capture screenshots without including personal save information. Do not mark translation records human-approved; report results for a later linguistic review.

## Open issues to report

- Character-creation prompts are not yet located in the extracted TextFile resources.
- Gender controls `0010 0003 1100 00FF 0202` and `0010 0003 1100 00FF 0403` are preserved but not decoded.
- Some source English strings contain U+FFFD in the catalog (`Pok�mon`, `It�s`). This reflects unresolved source decoding, not a claimed in-game glyph result.
