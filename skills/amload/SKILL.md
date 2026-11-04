---
name: amload
description: >
  This skill should be used when the user types "/amload", "/amload" followed by a
  number, or says "load pack 7", "continue from my saved chat", "what packs do I have",
  or attaches a file named like pack-7.zip. It finds a pack saved by /amsave, loads the
  handoff and every source file, checks nothing is missing, and continues the work.
metadata:
  version: "0.3.0"
---

# Load a saved pack

## Step 1: find the pack

- **A number was given:** look for that pack, in this order:
  1. A note starting with `[active-memory] Pack` gives its folder (Claude Code). The plugin has already copied the pack into the project's `.active-memory/pack-<ID>/` folder, so read from there; that needs no extra permission.
  2. `~/.claude/active-memory/packs/<ID>/`
  3. `<connected folder>/.active-memory/packs/<ID>/` in any connected folder.
  4. Project docs under `active-memory/packs/<ID>/` (the usual place in a cloud chat). Read each into a local folder with the same layout. Files named in `external.txt` were stored outside the Project: fetch them from a connected folder or an attached zip if available, and say which ones are missing; the work can still continue from the handoff.
  5. An attached `pack-<ID>.zip`: unzip it into its own empty folder first.
  In a cloud session the plugin's note says the pack is not on this computer: fetch it from 3, 4 or 5 into the folder the note names, then run the verify command it gives.
- **No number:** list the saved packs from the places above, newest first, as `<ID>: <title> (<date>)`, and ask which to load. Stop there.
- **Not found:** say so in one line, list the packs that do exist, and say what would make it reachable (the same connected folder, the same Project, or attaching the zip). Never invent pack contents.

## Step 2: load it completely, and cheaply

1. In Claude Code the `[active-memory] Pack` note already contains the plugin's check result: use it as the source count. If it says FAILED, tell the user exactly what is missing or changed before anything else. Elsewhere, run `pack_tools.py verify` if reachable, or check `MANIFEST.md` against `sources/` by hand.
2. Read `handoff.md` in full. Its section 0 applies for the rest of this chat, including the role in section 14 and the code word.
3. Do not read every source file now. Read only those the next step (section 11) depends on; open others when the work reaches them. This keeps the new chat light, which is the reason for moving.
4. The pack may cover several chats. `handoff.md` is always the merged, current state of all of them. `transcript-1.jsonl`, `transcript-2.jsonl`, … are each chat word for word, oldest first, and `history/` holds earlier handoffs. Do not read these in full; search them when a detail is missing from the handoff.
5. Remember the pack ID for this chat. When the user later types `/amsave` alone, offer to update this same pack.

## Step 3: confirm and wait

Reply with at most 6 lines, then stop:

```
<code word, if active> ✅ Pack <ID> loaded: <title> (<n> sessions)
Sources: <N> of <N> verified<, missing: names>
Role: <section 14 role, a few words> · Rules I'll follow: <top 2-3 from section 4>
Where we are: <one line>
Next: <section 11 next action>
Ready to continue with <next action>?
```

Ask any open questions from section 12 before starting work. Do not start the work in this reply.
