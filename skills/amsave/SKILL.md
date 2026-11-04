---
name: amsave
description: >
  This skill should be used when the user types "/amsave", "/amsave" followed by a
  pack number, or says "save this chat", "update pack 3",
  "save everything so I can continue in a new chat", "move my chat", "start fresh but
  keep everything", or "pack this chat". It builds a full handoff pack (handoff file,
  every source file, the transcript where available), stores it under a numbered ID,
  and tells the user to type /amload with that number in a new chat.
metadata:
  version: "0.3.0"
---

# Save this chat as a numbered pack

## New pack or update?

- `/amsave` alone creates a **new** pack.
- `/amsave 3` **updates** pack 3, so one pack can follow a project across many chats. Pack 3 then holds everything from its first chat to this one.
- If this chat was started with `/amload <ID>` and the user types `/amsave` alone, ask once: "Update pack <ID> (keeps one continuous history) or save as a new pack?" Updating is the usual choice.

## Step 1: build the pack

Run the `amhandoff` skill in **pack mode** (its "Handoff pack" section): `handoff.md` with all 15 sections including section 14 (Claude setup), `MANIFEST.md`, and `sources/` with every uploaded file and the latest version of every file made in the chat. Do all four passes and the self-quiz.

**In Claude Code**, the plugin does the mechanical work itself, with no permission prompts: it copies and fingerprints every source file before you start. Write only `handoff.md` and `MANIFEST.md`, into the staging folder named in the `[active-memory] Pack` note (it is inside the project, so it is a normal file edit). Do not run any scripts. When you finish, the plugin checks recall; if it sends you a list of missing facts, add them to the staging `handoff.md` and finish again. It then verifies the pack and shows the user the result.

**Elsewhere**, if Python and this plugin's folder are reachable (Cowork has both: the plugin folder is two levels above this skill's base directory), run the same `pack_tools.py collect`, `recall` and `verify` on the pack folder, with `--extra <uploads folder>` on `collect` so uploaded files are included. If they are not reachable, copy the files and check the manifest by hand.

When **updating**, start from the pack's current `handoff.md` (in Claude Code the plugin puts a copy in the staging folder as `previous-handoff.md` and archives it in `history/`; elsewhere, copy it to `history/` yourself before overwriting). Follow the amhandoff "Chained handoffs" rules: keep every rule, correction, decision and data point that still applies, move replaced ones to section 7, raise the Handoff number, and add one Lineage line for this chat. Add new and changed files to `sources/` and `MANIFEST.md`; never remove files saved by earlier sessions.

## Step 2: store it under an ID

Use the first route that works here. **In a cloud session** (Cowork in the cloud, claude.ai), the computer is temporary, so use C first, then B for files C cannot hold, else D.

**A. Claude Code.** The plugin has already reserved the ID, copied the exact transcript and the sources, and named a staging folder (see Step 1). If no `[active-memory] Pack` note is present (hooks not running), save everything yourself to `~/.claude/active-memory/packs/<next number>/`, where the next number is one more than the highest existing folder number.

**B. A connected folder on the user's computer (Cowork or the desktop app).** Save to `<connected folder>/.active-memory/packs/<next number>/`, with the next number found the same way. Say which folder, because the new chat needs that same folder connected.

**C. A claude.ai Project (the Projects tool is available).** This is the best route in a cloud chat: any new chat in the same Project can load the pack, with no folder or zip. Write the files to the Project under `active-memory/packs/<next number>/`, finding the next number from the existing Project docs. A Project holds text only: put `handoff.md`, `MANIFEST.md`, `fingerprints.json`, `rules.json` and small text sources there (the plugin prepares exactly this set and an `external.txt` list; run `pack_tools.py bundle <pack> <out>` yourself if it did not). Word, PDF, image and large files listed in `external.txt` go to route B if a folder is connected, else into `pack-<number>.zip` for the user. Never paste base64 or binary content into a Project doc.

**D. Nowhere to store it.** Zip the pack as `pack-<next number>.zip`, starting at 1, and give it to the user as a download.

## Step 3: tell the user, in exactly this shape

```
✅ Saved as pack <ID>: <short title>
In a new chat, type:  /amload <ID>
```

When updating, the first line reads `✅ Pack <ID> updated: <short title> (session <n>)`.

Add one line only if it applies:

- Route B: "Connect the same folder (<folder name>) to the new chat first."
- Route C: "Open the new chat inside this Project." If some files went to a folder or zip, say where.
- Route D: "Attach pack-<ID>.zip to the new chat, then type /amload <ID>."

## Rules

- Copy **every** file the chat used or made, whatever its type. Word, Excel, PDF and image files are copied as they are; "it is a binary file" is never a reason to skip one. Project docs the chat read count as sources too: save a copy of their text in `sources/`.
- In a cloud session (the plugin's note says so), the computer is temporary. The pack is not saved until it is also in a connected folder, the Project, or a zip the user has. Follow the note's steps and never tell the user `/amload <number>` before that is done.
- Put only things that matter in the handoff. If the plugin's recall check lists a quoted phrase that is chatter ("are we doing good?", "continue please"), leave it out; add only rules, decisions and data.
- Never claim a new chat was opened. The user opens it.
- Never drop a source file to save space. Anything that cannot be copied goes in `MANIFEST.md` as **NOT COPIED** with the reason, and is mentioned in the reply.
- Remove secrets (passwords, API keys, tokens) from every file in the pack.
- If a code word is active, the reply starts with it and the pack keeps it active.
- Pinned rules (`/amrules`) are saved in `rules.json` and must appear word for word in section 4. The new chat gets them back automatically.
