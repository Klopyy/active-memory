---
name: amhelp
description: >
  This skill should be used when the user types "/amhelp", or asks "what does
  active-memory do", "how do I use active-memory", "what are the active-memory
  commands", or "help with amcodeword / amcheckpoint / amhandoff". It shows a short
  guide to every active-memory command plus one tip tailored to the current chat.
metadata:
  version: "0.1.0"
---

# active-memory help

Show the guide below. Adapt its language to the user's. If a code word is active in this chat, the reply still starts with it.

## Guide to show

```
🧠 **active-memory: keeps long chats on track**

Long chats make Claude slowly lose track of early details. active-memory warns you when that starts, and moves your work to a fresh chat without losing anything.

To use a command, type it in the chat box like a normal message.

| Command | What it does | When to use it |
|---|---|---|
| `/amcodeword` | Claude starts every reply with **Yes Boss!** Use `/amcodeword Your phrase` for your own, `/amcodeword off` to stop, `/amcodeword status` to check | At the start of any chat you expect to be long |
| `/amcheckpoint` | A quick recap of the chat so far, plus a 🟢🟡🔴 health check | When replies feel off, or every ~20 messages |
| `/amhandoff` | Writes a complete handoff file so a new chat continues exactly where you left off | When the code word goes missing, you see 🔴, or you're stopping for the day |
| `/amhelp` | Shows this guide | Anytime |

**The usual flow**
1. Type `/amcodeword` at the start of a chat.
2. Work normally.
3. A reply arrives **without** "Yes Boss!" → type `/amhandoff`.
4. Open a new chat, attach the handoff file (plus any files it lists), and send **continue**.
5. The new chat replies with a short summary and waits for your go.

**Good to know**
- The code word is a warning sign, not a guarantee. `/amcheckpoint` also warns you on its own at ~20 and ~35 messages.
- Files you uploaded don't carry over to a new chat. The handoff file lists which ones to attach again.
- Running `/amhandoff` in a chat that started from a handoff file updates that file (#2, #3…) so your history keeps growing.
- None of this gives Claude memory across chats. It makes the move between chats complete.
```

## Tip for this chat

After the guide, add exactly one line that fits the current chat, picked in this order:

1. A code word was set and a recent reply was missing it → "🔴 A reply in this chat was missing the code word. Run `/amhandoff` now."
2. The chat is long (about 35+ exchanges) → "🔴 This chat is already long. `/amhandoff` is a good idea now."
3. The chat is fairly long (about 20+ exchanges) → "🟡 This chat is getting long. Try `/amcheckpoint`."
4. No code word active → "💡 The code word is off in this chat. Type `/amcodeword` to turn it on."
5. Otherwise → "✅ Code word is on and this chat is still short. You're all set."

If the user asked about one command only, show just that row with a 2-3 line example of using it, followed by the tip line.
