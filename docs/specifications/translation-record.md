# Translation Record Specification (Draft)

Each extracted message record must include a stable ID, source text, source language, target scope (`shared`, `x`, or `y`), source game/version and relative path, archive/member/message indices, source resource hash, context, raw control-code signature, translation text, and one status: `untranslated`, `machine_draft`, `reviewed`, `validated`, or `tested_in_game`.

Equal source wording does not establish shared identity. Sharing requires equivalent context, placeholders, and formatting. Machine-generated drafts must never be marked reviewed.
