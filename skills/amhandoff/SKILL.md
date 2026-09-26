---
name: amhandoff
description: >
  This skill should be used when the user types "/amhandoff", or asks to "move to
  a new chat", "continue in a new chat", "make a handoff file", "save this chat
  so I can continue later", "export the context", or when a checkpoint is red or
  the code word went missing. It reads the whole chat in four passes and writes a
  complete handoff.md so a fresh chat is fully up to speed from its first reply.
  It should also be used when a user attaches or pastes a file that starts with
  "# active-memory handoff".
metadata:
  version: "0.2.0"
---

# Handoff

Write a handoff file so complete that a brand-new chat with no access to this one can continue the work at full quality from its first reply: same rules, same style, same exact data, same next step, and none of the mistakes already corrected.

A plain "write a handoff.md" request produces a summary drawn mostly from recent messages. It loses early rules, corrections, rejected ideas, and exact figures. Prevent that by following the four passes below, every time, in order.

The file layout is fixed and given in **The file** section below. Use it exactly: same title line, same 14 headings (0-13) in the same order, same section 0 text. Worked examples of good and bad extraction are in `references/extraction-guide.md`. Read it when unsure how to capture something.

## Pass 1: Scan (message 1 → last)

Go through the conversation **from the very first message to the last**, in order. Do not start from the recent end. For every message, record anything that belongs in sections 1-13 of the file. Treat these as always important:

- Every instruction about how Claude should behave or write, even if said once in passing ("don't use emojis", "keep it RTL", "never start with Okay").
- Every time the user corrected Claude: what Claude did, what the user wanted instead.
- Every rejected idea or replaced decision, with the reason when one was given.
- Every exact value: numbers, prices, currencies, dates, measurements, IDs, names, spellings, file names, paths, URLs, versions, commands, colors, fonts.
- Every file, document, artifact, or piece of code created or uploaded, and its latest state.
- The user's own words for things (nicknames, abbreviations, project names).
- Anything uploaded that the new chat will need again.

Copy rules and data **word for word**. Summarize only discussion.

## Pass 2: Reconcile

- For each topic, the **latest** statement from the user wins. Put the replaced version in section 7 (Changed / rejected) with an arrow: `old → new`.
- Separate what the **user** decided from what Claude only **suggested**. Claude's unaccepted suggestions are not decisions.
- Merge duplicates. Keep the most exact wording.
- **Conflicts:** if two statements disagree and the chat never settles which one wins (for example two different prices for the same item with no clear "final"), **stop and ask the user before writing the file.** Ask 1-3 short, numbered questions at most, each with the candidate answers. Offer "skip, flag it in the file" as an option. Wait for the reply, then continue. If there are no real conflicts, ask nothing.

## Pass 3: Gap check

Pretend to be a fresh Claude reading only the draft. For each section ask: "What would I still have to ask the user, or what could I get wrong?" Then:

- Fill the gap from the chat if the answer is there.
- If the answer is not in the chat, list it under section 12 (Open questions). Never invent it.
- Make sure **section 11** names one concrete next action, not "continue the work".
- Make sure a reader could reproduce the style from section 3 alone: language, tone, length, formatting, what to avoid.

## Pass 4: Self-audit

Check before delivering:

- [ ] The title line and all headings 0-13 match the template exactly, in order. Empty sections say "None."
- [ ] Section 5 lists every correction as a table row, even small ones.
- [ ] Every hard rule and every correction from the chat appears.
- [ ] Every number, price, and name matches the chat exactly.
- [ ] Nothing depends on the old chat ("as discussed above", "the file from before").
- [ ] Secrets (passwords, API keys, tokens, card numbers) are replaced with `[secret removed: re-enter it]`.
- [ ] Files that must be attached again are listed in section 13.
- [ ] The boot instructions in section 0 are unchanged from the template, with the code-word line filled in.

Fix anything unchecked, then write the audit line at the bottom of the file as the template shows. Do not add a separate checklist to the file.

## The file

Write the handoff file with exactly this structure. Replace everything in `<angle brackets>`. Keep headings and the section 0 text as written (only fill in its placeholders). Use the chat's main language for the content. Keep the headings in English so the file stays recognizable.

Write compact lines, one fact per bullet. Use tables for data with more than 3 rows. Inline small, critical code or data (up to about 50 lines). For anything larger, describe it and list the file in section 13 instead of pasting it.

````markdown
# active-memory handoff: <project or chat title>

**Handoff #<n>** · <YYYY-MM-DD> · Lineage: <#1 (date): one-line summary>; <#2 …>

## 0. Instructions for Claude (read first)

You are continuing work from a previous chat. That chat is gone; this file is the complete context and the source of truth.

1. Read this whole file before replying.
2. Follow sections 3 (Style), 4 (Hard rules) and 5 (Corrections) in every reply, for the rest of this chat. They override your defaults.
3. Use the values in section 8 exactly. Never round, re-estimate, or "correct" them.
4. Do not suggest anything listed in section 7 (Changed / rejected) again unless the user brings it up.
5. Code word: <Start every reply with exactly "PHRASE" | None active. If the user types /amcodeword, start every reply with the phrase they choose (default "Yes Boss!")>.
6. Your first reply: at most 5 lines covering the goal, the current state, and the next step (section 11). Mention any files from section 13 that were not attached. Ask the questions in section 12 if there are any. End with "Ready to continue with <next step>?" Then wait for the user's go.

## 1. Mission
- **Goal:** <what is being built or solved>
- **Done looks like:** <how the user will judge it finished>
- **Why it matters / context:** <one line, if stated>

## 2. About the user (as relevant to this work)
- <role, organization, domain, skill level, tools they use, audience they build for>

## 3. Style & communication
- **Language:** <e.g. English replies; Arabic RTL for all UI text>
- **Tone:** <e.g. direct, friendly, no fluff>
- **Reply length:** <e.g. short; details only when asked>
- **Formatting:** <headings, tables, bullets, code blocks, emojis yes/no>
- **Working style:** <e.g. brainstorm before building; ask before big steps; one question at a time>
- **Avoid:** <things the user dislikes>

## 4. Hard rules (word for word)
1. "<exact rule>" <(context, if needed)>
2. …

## 5. Corrections log
| # | Claude did | The user wanted |
|---|---|---|
| 1 | <mistake> | <correction, exact> |

## 6. Decisions
| Decision | Why |
|---|---|
| <final choice> | <reason, or "user's call"> |

## 7. Changed / rejected
- <old> → <new> (<reason>)
- ❌ <rejected idea> (<reason>)

## 8. Data & facts (exact)
<tables or bullets of numbers, prices, dates, IDs, measurements, specs>

## 9. People, terms & names
- **People:** <name: role / relation to the work>
- **Terms & nicknames:** <term = meaning>
- **Names in use:** <file names, variable names, product names, commands, exact spellings>

## 10. Work state
| Item | Status | Version / location | Notes |
|---|---|---|---|
| <file, doc, feature> | <final / draft / not started> | <v, path, link> | <what's left> |

<Small, critical snippets inline here if needed.>

## 11. Next steps
1. **Next action:** <one concrete step>
2. <then…>

## 12. Open questions ⚠️
- <unresolved item, with the candidate answers>
<or "None.">

## 13. Re-attach checklist
- [ ] <file name>: <why the new chat needs it>
<or "Nothing to attach.">

---
<sub>Audit: 13/13 sections · <N> rules · <N> corrections · <N> data points · secrets removed: <yes/none found> · generated by active-memory</sub>
````

## Chained handoffs

If this chat itself started from an active-memory handoff file:

- Start from that file. Do not rebuild from zero.
- Increase the number: `Handoff #2`, `#3`…
- Apply the four passes to the messages since the file was loaded, then update every section. Move replaced items to section 7. Keep older history that still matters.
- Add one line to the **Lineage** field: `#<n> (<date>): <one-line summary of what this chat did>`.

## Delivery

1. Name the file `handoff.md`. If the chat is clearly about a named project, use `handoff-<project-name>.md` in lowercase with hyphens.
2. Save it as a real file the user can download when file creation is available. In a coding tool, save it in the current project or working folder (never a temporary or scratch folder) and say where it is. Otherwise output the whole file in one single code block so it can be copied in one go.
3. After the file, show exactly this short guide in the user's language (and nothing long before it):

```
✅ **Handoff ready.** Next:
1. Download `<file name>` <or, if it was saved in a folder: "Find `<file name>` in <folder>">.
2. Open a new chat and attach it<, together with: <files from section 13>>.
3. Send: **continue**
The new chat will reply with a short summary and wait for your go.
```

If a code word is active, this reply also starts with it.

## Resuming from a handoff file (in the new chat)

When a user attaches or pastes a file that starts with `# active-memory handoff`:

1. Read the entire file before replying. Its section 0 instructions apply for the rest of the chat.
2. Treat sections 3, 4, and 5 as binding rules and section 8 as exact data.
3. If section 0 names an active code word, start this reply and every later reply with it.
4. Reply with a confirmation of at most 5 lines: the goal, the latest state, the next step, and any files from section 13 that were not attached. Then ask the open questions from section 12 if any exist, and end with "Ready to continue with <next step>?"
5. Wait for the user's go. Do not start the work in the same reply.
