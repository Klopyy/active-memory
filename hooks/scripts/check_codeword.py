#!/usr/bin/env python3
"""Stop hook: warns the USER (not Claude) when a reply doesn't start with the code word.

Output is a systemMessage, which Claude Code shows to the user. Nothing is fed back
to Claude, so the code word stays a real memory test.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402

LEADING_NOISE = re.compile(r"^[\s*_#>`~\-]+")


def _is_real_prompt(entry):
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        types = {c.get("type") for c in content if isinstance(c, dict)}
        return "tool_result" not in types and bool(types & {"text", "image", "document"})
    return False


def turn_texts(transcript_path):
    """Assistant texts written after the latest real user prompt, in order."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except (OSError, ValueError):
        return []
    last_prompt = -1
    for i, e in enumerate(entries):
        if _is_real_prompt(e):
            last_prompt = i
    texts = []
    for e in entries[last_prompt + 1:]:
        if e.get("type") != "assistant":
            continue
        content = (e.get("message") or {}).get("content")
        if isinstance(content, str) and content.strip():
            texts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                    texts.append(c["text"])
    return texts


def _same(a, b):
    return a.strip()[:200] == b.strip()[:200]


def reply_start(transcript_path, last_message):
    """Text that should start with the code word: the first text of this turn.

    The transcript can lag behind the Stop event, so only trust it once its
    last text matches last_assistant_message; otherwise judge last_assistant_message.
    """
    for _ in range(10):
        texts = turn_texts(transcript_path) if transcript_path else []
        if texts and (not last_message or _same(texts[-1], last_message)):
            return texts[0]
        if not last_message and not transcript_path:
            return None
        time.sleep(0.2)
    return last_message or None


def starts_with_phrase(text, phrase):
    cleaned = LEADING_NOISE.sub("", text)
    return cleaned.lower().startswith(phrase.lower())


def main():
    data = state.read_stdin_json(sys.stdin)
    if os.environ.get("ACTIVE_MEMORY_DEBUG"):
        with open(os.path.join(state.state_dir(), "stop_debug.jsonl"), "a") as f:
            f.write(json.dumps(data) + "\n")
    if data.get("stop_hook_active"):
        return
    session = data.get("session_id", "unknown")
    st = state.load(session)
    phrase = st.get("codeword")
    if not phrase:
        return
    last_message = data.get("last_assistant_message") or ""
    text = reply_start(data.get("transcript_path"), last_message)
    if not text or not text.strip():  # tool-only turn or nothing readable: nothing to judge
        return

    if starts_with_phrase(text, phrase):
        return

    st["misses"] = int(st.get("misses", 0)) + 1
    state.save(session, st)
    msg = (
        "🐤 active-memory: that reply was missing your code word. "
        "Claude may be losing track of this chat. Run /amhandoff to move to a fresh chat, "
        "or /amcheckpoint for a quick recap."
    )
    print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
