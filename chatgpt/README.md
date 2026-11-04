# active-memory on ChatGPT

The Claude plugin uses Claude Code hooks and slash commands, which ChatGPT does not have. What carries over is the core idea: the four-pass handoff, the checkpoint, the code word and pinned rules, as plain instructions.

| You want | Use | Where |
|---|---|---|
| Full version, always on | [`active-memory-instructions.md`](active-memory-instructions.md) | A Custom GPT (Instructions), a Project (Project instructions), or pasted at the start of one chat |
| Quick setup in every chat | [`custom-instructions-short.txt`](custom-instructions-short.txt) | Settings > Personalization > Custom Instructions |

## How to use it

1. Paste the instructions (see the table).
2. In a long chat, type **amhandoff**. ChatGPT reads the whole chat and writes the handoff file in one code block.
3. Save it as `handoff.md`. Open a new chat, paste or attach the file and send **continue**.

Handoff files use the same format on both sides, so a file written by Claude works in ChatGPT and the other way round.

## What is different from Claude

- Commands are typed words (`amhandoff`), not slash commands.
- No hooks: ChatGPT cannot count messages or check the code word for you, so it relies on the instructions.
- No `/amsave` and `/amload` packs: copy the files your chat used yourself and re-attach them in the new chat (section 13 of the handoff lists them).
- The method is the same, but ChatGPT cannot run the plugin's script checks (word cap, fingerprints, verify).
