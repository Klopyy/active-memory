"""Shared per-session state for active-memory hooks.

State lives in ~/.claude/active-memory/sessions/<session_id>.json
(override the folder with ACTIVE_MEMORY_STATE_DIR). It is never shown to Claude.
"""
import json
import os
import re

DEFAULT_PHRASE = "Yes Boss!"
NUDGE_AT = (20, 35)


def state_dir():
    base = os.environ.get("ACTIVE_MEMORY_STATE_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude", "active-memory", "sessions"
    )
    os.makedirs(base, exist_ok=True)
    return base


def _path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return os.path.join(state_dir(), safe + ".json")


def load(session_id):
    try:
        with open(_path(session_id), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"turns": 0, "codeword": None, "misses": 0}


def save(session_id, data):
    tmp = _path(session_id) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, _path(session_id))


def read_stdin_json(stream):
    try:
        return json.loads(stream.read() or "{}")
    except ValueError:
        return {}
