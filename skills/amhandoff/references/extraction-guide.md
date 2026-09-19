# Extraction guide: good vs. bad

Use these contrasts when deciding how to capture something in the handoff file.

## Rules: copy, don't soften

| Chat said | ❌ Bad | ✅ Good |
|---|---|---|
| "never use the word 'Okay' at the start" | Keep replies professional | "never use the word 'Okay' at the start" |
| "all UI text Arabic, RTL, numbers stay Western digits" | Arabic interface | "all UI text Arabic, RTL, numbers stay Western digits" |

## Data: exact, with units

| Chat said | ❌ Bad | ✅ Good |
|---|---|---|
| Lifting is 1,250 EGP per meter, min 8 m | About 1,200 EGP/m | Lifting: 1,250 EGP per meter · minimum 8 m |
| Deadline moved from Oct 3 to Oct 10 | Deadline early October | Deadline: 2026-10-10 (section 7: 2026-10-03 → 2026-10-10) |

## Corrections: capture both sides

A correction is the single most valuable line in a handoff. Without it, the new chat repeats the mistake.

- ❌ "Fixed the table layout."
- ✅ `| 3 | Put the total column on the right | Total column goes on the LEFT (RTL table) |`

## Decisions vs. suggestions

- Claude proposed three names and the user said "go with the second" → only the second is a decision. The other two go to section 7 as rejected.
- Claude suggested adding dark mode and the user never answered → not a decision. Put it in section 12 only if it still matters.

## Implicit style

Style is often shown, not stated. Record it when the pattern is clear:

- The user always writes short messages and gets annoyed at long replies → "Reply length: short".
- The user asked twice to "just show the code" → "Formatting: code first, minimal explanation".

Mark inferred style with "(observed)" so the new chat knows it wasn't a stated rule.

## Work state: latest version only

If a file went through v1, v2, v3, record v3 as the current state, with any still-relevant reason for the changes. Don't narrate the history.

## Things that can't transfer

- Uploaded files, images, and generated downloads → section 13.
- Links to artifacts the user can reopen → section 10 with the link.
- Secrets → `[secret removed: re-enter it]`.

## Too long?

Keep all rules, corrections, decisions, and exact data. Shorten only discussion, background, and "done" items. Never drop a rule or a correction to save space.
