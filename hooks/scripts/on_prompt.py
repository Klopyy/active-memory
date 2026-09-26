#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UserPromptSubmit hook. Runs on any Python (2.7 and every 3.x).

1. Reads /amcodeword commands and stores the phrase (never echoed back to Claude).
2. Counts exchanges and, at 20 and 35, adds a note asking Claude to run a checkpoint.
Never blocks the prompt. Any error exits quietly.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402

CODEWORD_RE = re.compile(r"^\s*/(?:active-memory:)?amcodeword\b(.*)$", re.IGNORECASE | re.DOTALL)


def parse_codeword(prompt):
    """Return ('on', phrase) | ('off', None) | ('status', None) | None."""
    m = CODEWORD_RE.match(prompt or "")
    if not m:
        return None
    arg = m.group(1).strip()
    if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in "\"'“”":
        arg = arg[1:-1].strip()
    elif len(arg) >= 2 and arg[0] == "“" and arg[-1] == "”":
        arg = arg[1:-1].strip()
    if not arg:
        return ("on", state.DEFAULT_PHRASE)
    if arg.lower() == "off":
        return ("off", None)
    if arg.lower() == "status":
        return ("status", None)
    return ("on", arg)


def main():
    data = state.read_stdin_json(sys.stdin)
    session = data.get("session_id", "unknown")
    prompt = data.get("prompt", "")
    st = state.load(session)

    cmd = parse_codeword(prompt)
    if cmd:
        action, phrase = cmd
        if action == "on":
            st["codeword"] = phrase
            st["misses"] = 0
        elif action == "off":
            st["codeword"] = None

    st["turns"] = int(st.get("turns", 0)) + 1
    state.save(session, st)

    if st["turns"] in state.NUDGE_AT:
        level = "yellow" if st["turns"] == state.NUDGE_AT[0] else "red"
        note = (
            "[active-memory] This chat has reached {0} exchanges. "
            "First reply to the user's message exactly as you normally would, following every "
            "rule of this chat. Then, at the end of that same reply, append a checkpoint "
            "(amcheckpoint skill) with health at least {1}. Do not replace the answer with it."
        ).format(st["turns"], level)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": note,
            }
        }))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # never break the user's chat
        pass
    sys.exit(0)
