---
name: amcodeword
description: >
  This skill should be used when the user types "/amcodeword", "/amcodeword off",
  "/amcodeword status", "/amcodeword" with a phrase after it, or asks to "set a code
  word", "start every reply with",
  "turn on the code word", or "turn off the code word". It makes Claude open
  every reply with a fixed phrase (default "Yes Boss!") so the user can spot the
  moment Claude starts losing track of a long chat: the phrase goes missing.
metadata:
  version: "0.2.1"
---

# Code word

The code word is an early-warning sign for long chats. Claude opens every reply with a fixed phrase. Following an instruction given many messages ago is exactly what gets weaker as a chat grows, so the first reply that forgets the phrase tells the user the chat is drifting. The user does not have to trust Claude's own judgment about whether it is losing track.

## Read the argument

Take the text after the command (the arguments):

- **Empty** → turn on with the default phrase **`Yes Boss!`**
- **`off`** (any case) → turn off
- **`status`** → report whether a code word is active in this chat and what it is
- **Anything else** → turn on with that exact text as the phrase. Strip one pair of surrounding quotes if present. Keep the user's capitalization and punctuation exactly.

If the user asked in plain words ("start every reply with Yes Boss!") instead of the command, extract the phrase the same way.

## Turn on

1. Start this very reply with the phrase, exactly as written, followed by a space.
2. Confirm in 2-4 short lines, in the user's language:
   - The phrase that is now active.
   - What it is for: "If a reply ever shows up without it, I'm starting to lose track of this chat. Run `/amhandoff` to move to a fresh chat, or `/amcheckpoint` for a quick recap."
   - How to turn it off: `/amcodeword off`.
3. From now until the user turns it off, begin **every** reply with the exact phrase, including very short replies, replies that only contain code, error messages, and replies after tool use. Never paraphrase, translate, or restyle it.

If the user's phrase is one Claude already tends to start replies with naturally ("Okay", "Sure", "Great", "Got it"), mention in one line that a missing phrase would be harder to spot, and suggest the default `Yes Boss!`. Still use the user's choice if they keep it.

## Turn off

Reply without the phrase. Confirm in one line that the code word is off and that `/amcodeword` turns it back on.

## Changing the phrase

Setting a new phrase replaces the old one at once. Start the confirming reply with the new phrase.

## When the user reports a missing code word

If the user says a reply was missing the phrase ("you forgot Yes Boss!", "where's the code word?"):

First check the previous reply. If it did start with the phrase, say so in one line and continue normally.

If it really was missing:

1. Do not just apologize and add it back. The miss is the signal the user asked for.
2. Start the reply with the phrase again.
3. Say plainly, in one line, that the miss means the chat has grown long enough to lose track.
4. Run the `amcheckpoint` skill with the health forced to 🔴 Red, and recommend `/amhandoff` now.

## Rules

- Never tell the user the code word proves that Claude remembers everything. It is a warning sign, not a guarantee.
- The code word applies only to this chat. A new chat starts without it unless a handoff file turns it on.
- In Claude Code, the plugin's hooks read the phrase from the `/amcodeword` command and check each reply for it. They never repeat the phrase back to Claude, so remembering it stays a real test.
