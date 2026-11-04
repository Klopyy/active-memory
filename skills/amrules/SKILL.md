---
name: amrules
description: >
  This skill should be used when the user types "/amrules", "/amrules" followed by a rule,
  "/amrules remove 2", "/amrules clear", or says "pin this rule", "never forget this rule",
  "always follow this", "what rules are pinned", or "unpin rule". It keeps a short list of
  pinned rules that Claude re-reads before every reply, so they cannot drift in a long chat,
  and carries them into new chats through /amsave and /amload.
metadata:
  version: "0.3.0"
---

# Pinned rules

Long chats bury early instructions. A pinned rule is re-read before **every** reply, so it holds at message 5 and at message 80.

## Commands

| Type | Result |
|---|---|
| `/amrules` | Shows the pinned rules as a numbered list |
| `/amrules <rule>` or `/amrules add <rule>` | Pins the rule, word for word |
| `/amrules remove 2` | Unpins rule 2 |
| `/amrules clear` | Unpins all of them |

Up to 15 rules, each one line. Suggest pinning only rules that must never drift (exact prices and formats, "never do X", naming rules), because the list is re-sent with every message.

## How it works

**In Claude Code** the plugin stores the list and adds it to every message as an `[active-memory] Pinned rules` note. Follow every pinned rule in every reply. When a `/amrules` command arrives, the note says what changed: confirm in one line and show the list.

**Elsewhere** (no plugin note), keep the list yourself:
- When a rule is pinned, repeat the full numbered list in your reply.
- Before each reply, check your draft against every pinned rule.
- Repeat the list in every checkpoint, so it stays near the end of the chat.

## Rules

- Never pin something the user did not ask to pin. You may suggest it in one line ("Want me to pin that with /amrules?") when the user states a rule that clearly must last.
- If a new instruction conflicts with a pinned rule, follow the pinned rule and ask once whether to update it.
- `/amsave` saves the list in the pack (`rules.json`) and in section 4 of the handoff. `/amload` pins them again in the new chat.
- If a code word is active, the reply starts with it.
