---
name: amhelp
description: >
  This skill should be used when the user types "/amhelp", or asks "what does
  active-memory do", "how do I use active-memory", "what are the active-memory
  commands", or "help with amcodeword / amcheckpoint / amhandoff / amsave / amload / amrules / amsetup". It shows a short
  guide to every active-memory command plus one tip tailored to the current chat.
metadata:
  version: "0.3.0"
---

# active-memory help

Show the guide below. Adapt its language to the user's. If a code word is active in this chat, the reply still starts with it.

## Guide to show

```
🧠 **active-memory: move to a fresh chat without losing anything**

Long chats make Claude slowly lose track of early details. active-memory moves your work to a fresh chat without losing a single rule, correction or number, and warns you when it is time to switch.

To use a command, type it in the chat box like a normal message.

| Command | What it does | When to use it |
|---|---|---|
| `/amcodeword` | Claude starts every reply with **Yes Boss!** Use `/amcodeword Your phrase` for your own, `/amcodeword off` to stop, `/amcodeword status` to check | At the start of any chat you expect to be long |
| `/amcheckpoint` | A quick recap of the chat so far, plus a 🟢🟡🔴 health check | When replies feel off, or every ~20 messages |
| `/amhandoff` | Writes a complete handoff file so a new chat continues exactly where you left off | When the code word goes missing, you see 🔴, or you're stopping for the day |
| `/amsave` | Saves the whole chat, with every file, as a numbered pack. `/amsave 3` adds this chat to pack 3 | When the chat is long and you want a fresh one |
| `/amload 7` | Loads pack 7 into a new chat. `/amload` alone lists your packs | First message of the new chat |
| `/amrules` | Pins a rule Claude re-reads before every reply. `/amrules` lists them, `/amrules remove 2`, `/amrules clear` | For rules that must never drift: prices, formats, "never do X" |
| `/amhelp` | Shows this guide | Anytime |
| `/amsetup` | Checks what the plugin needs on this computer and fixes it | If something isn't working |

**The usual flow**
1. Type `/amcodeword` at the start of a chat.
2. Work normally.
3. A reply arrives **without** "Yes Boss!" → type `/amsave`. It answers with a pack number, say 7.
4. Open a new chat and type `/amload 7`.
5. The new chat confirms every file loaded and waits for your go.

**Good to know**
- The code word is a warning sign, not a guarantee. `/amcheckpoint` also warns you on its own at ~20 and ~35 messages.
- Files you uploaded don't carry over to a new chat. The handoff file lists which ones to attach again.
- Running `/amhandoff` in a chat that started from a handoff file updates that file (#2, #3…) so your history keeps growing.
- None of this gives Claude memory across chats. It makes the move between chats complete.
```

## Tip for this chat

After the guide, add exactly one line that fits the current chat, picked in this order:

1. A code word was set and a recent reply was missing it → "🔴 A reply in this chat was missing the code word. Run `/amsave` now."
2. The chat is long (about 35+ exchanges) → "🔴 This chat is already long. `/amsave` is a good idea now."
3. The chat is fairly long (about 20+ exchanges) → "🟡 This chat is getting long. Try `/amcheckpoint`."
4. No code word active → "💡 The code word is off in this chat. Type `/amcodeword` to turn it on."
5. Otherwise → "✅ Code word is on and this chat is still short. You're all set."

If the user asked about one command only, show just that row with a 2-3 line example of using it, followed by the tip line.
