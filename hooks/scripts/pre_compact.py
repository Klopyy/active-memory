#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PreCompact hook (any Python 2.7 or 3.x): saves the full transcript before Claude Code
compacts it, so nothing from a long chat is lost even without a handoff."""
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402


def main():
    data = state.read_stdin_json(sys.stdin)
    src = data.get("transcript_path")
    if not src or not os.path.isfile(src):
        return
    dest = os.path.join(os.path.dirname(state.packs_dir()), "transcripts")
    try:
        os.makedirs(dest)
    except OSError:
        pass
    shutil.copyfile(src, os.path.join(dest, "before-compact-" + time.strftime("%Y%m%d-%H%M%S") + ".jsonl"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
