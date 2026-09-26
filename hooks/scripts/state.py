# -*- coding: utf-8 -*-
"""Shared per-session state for active-memory hooks.

Runs on any Python (2.7 and every 3.x). No third-party packages.
State lives in ~/.claude/active-memory/sessions/<session_id>.json
(override the folder with ACTIVE_MEMORY_STATE_DIR). It is never shown to Claude.
"""
import io
import json
import os
import re

DEFAULT_PHRASE = "Yes Boss!"
NUDGE_AT = (20, 35)


def state_dir():
    base = os.environ.get("ACTIVE_MEMORY_STATE_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude", "active-memory", "sessions"
    )
    try:
        os.makedirs(base)
    except OSError:
        pass  # already there, or cannot be created
    return base


def _path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "unknown")
    return os.path.join(state_dir(), safe + ".json")


def load(session_id):
    try:
        f = io.open(_path(session_id), encoding="utf-8")
        try:
            return json.load(f)
        finally:
            f.close()
    except (IOError, OSError, ValueError):
        return {"turns": 0, "codeword": None, "misses": 0}


def save(session_id, data):
    path = _path(session_id)
    tmp = path + ".tmp"
    text = json.dumps(data, ensure_ascii=False)
    if not isinstance(text, type(u"")):  # Python 2 gives str here
        text = text.decode("utf-8")
    f = io.open(tmp, "w", encoding="utf-8")
    try:
        f.write(text)
    finally:
        f.close()
    try:
        os.remove(path)  # Python 2 cannot replace an existing file
    except (IOError, OSError):
        pass
    os.rename(tmp, path)


def read_stdin_json(stream):
    try:
        raw = stream.read()
        if hasattr(raw, "decode"):
            try:
                raw = raw.decode("utf-8")
            except AttributeError:
                pass
        return json.loads(raw or "{}")
    except (ValueError, IOError, OSError, UnicodeDecodeError):
        return {}
