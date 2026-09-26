---
name: amcheckpoint
description: >
  This skill should be used when the user types "/amcheckpoint", or says "recap",
  "summary so far", "where are we", "are you losing track", "you forgot",
  "we already decided that", or points out a missing code word. It should also be
  used without being asked when a chat reaches about 20 or 35 exchanges, when
  large files or pastes pile up, or when Claude contradicts or forgets something
  already settled. It writes a compact recap of the chat plus a green, yellow, or
  red health check.
metadata:
  version: "0.2.3"
---

# Checkpoint

Long chats get less reliable because details from early messages get less attention. Rewriting the essentials in a short recap puts them back in focus. The health check tells the user honestly whether a fresh chat is due.

## When to run

**On request:** always, whenever the user runs `/amcheckpoint` or asks for a recap.

**Without being asked,** at a natural break (never in the middle of a multi-step tool run), when any of these happen:

| Signal | Health |
|---|---|
| About 20 exchanges | 🟡 Yellow at least |
| About 35 exchanges | 🔴 Red |
| The user corrects something already decided, or Claude re-asks a settled question, forgets a name, file, rule, or language/format preference | 🔴 Red |
| The user reports a missing code word | 🔴 Red |
| Many large pastes, files, images, or long generated outputs | Raise one level |
| A context or token budget is visible: over ~50% used / over ~75% used | 🟡 / 🔴 |

When running without being asked, **first answer the user's current message in full**, then add the checkpoint below it. Never replace the answer with the checkpoint.

Do not run automatically more than once per stage. After a checkpoint at 20, wait for the next stage (35), a correction, or a request. In Claude Code, a hook may add a note saying the exchange count reached 20 or 35. Treat that note as the signal.

## Steps

1. Re-read the whole conversation from the first message. Give extra weight to the early messages and to every time the user corrected Claude.
2. Pull out only what is needed to keep working. Copy names, numbers, prices, file names, versions, and rules exactly. Never round, paraphrase a rule, or fill gaps with guesses. Write "none yet" for an empty section.
3. When two parts of the chat disagree, the latest statement from the user wins. Move the older one to **Changed / rejected**.
4. Pick the health level from the table above. Be honest: if a mistake came from losing track, say so.
5. Write the checkpoint in the user's language using the format below, with **every** section in it (write "none yet" for empty ones). Put each correction the user made under **Rules to remember** so it is not repeated. If a code word is active, the reply still starts with it.
6. From here on, treat the recap as the source of truth. If the user corrects the recap, fix it and follow the correction.

## Format

```
📌 **Chat checkpoint: <🟢 Green | 🟡 Yellow | 🔴 Red>**

**Goal:** <1-2 lines: what is being built or solved>

**Decisions made:**
- <final choices only>

**Changed / rejected:**
- <older choice → what replaced it, or idea rejected>

**Key details:** <exact names, files, numbers, versions, formats, language/RTL rules>

**Done so far:** <short bullets>

**Open / next steps:**
1. <in order>

**Rules to remember:** <the user's stated preferences and constraints>

<⚠️ or ✅> **Health:** <one sentence>
```

Then add the lines that apply:

- **Yellow:** "💡 This chat is getting long. Consider `/amhandoff` at the next good stopping point."
- **Red:** "🔴 I'd move to a fresh chat now. Run `/amhandoff` and I'll write a file that brings the new chat fully up to speed."
- **No code word active in this chat:** "💡 The code word is off in this chat. Type `/amcodeword` and I'll start every reply with 'Yes Boss!', so you'll notice if I start losing track."

If the user asked for no emojis, replace the emojis with plain words (for example "Health: Yellow").

Keep the recap under about 300 words. It is a refresher, not the handoff file. For a full transfer to a new chat, the `amhandoff` skill does a much deeper pass.

## Rules

- Never invent details. Never include passwords, API keys, or other secrets. Write "[secret removed]" instead.
- A checkpoint does not reset memory. Do not claim it does.
- Green means "fine for now", not "nothing can be missed".
