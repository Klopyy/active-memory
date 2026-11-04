#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UserPromptSubmit hook. Runs on any Python (2.7 and every 3.x).

1. Reads /amcodeword commands and stores the phrase (never echoed back to Claude).
2. Counts exchanges and, at 20 and 35, adds a note asking Claude to run a checkpoint.
Never blocks the prompt. Any error exits quietly.
"""
import io
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402
import pack_tools  # noqa: E402

RUN_STEPS = (
    "Sources are already copied and fingerprinted ({collected}). Do NOT run any scripts.\n"
    "Write handoff.md and MANIFEST.md into this folder inside the project: {staging}\n"
    "When you finish, the plugin moves them into the pack, checks recall and verifies it, and "
    "tells you if any fact is missing."
)

CLOUD_SAVE = (
    "\nCloud session: this computer is temporary. The number above is only a working number; "
    "{pick} When the save is verified, the plugin will tell you where to store the pack so any new chat "
    "can load it."
)
CLOUD_LOAD = (
    "[active-memory] Cloud session: pack {0} is not on this temporary computer. Look in this order:\n"
    "1. The Project: with the Projects tool, project_read every doc under active-memory/packs/{0}/ and "
    "write each into {1} at the same relative path (handoff.md, MANIFEST.md, fingerprints.json, rules.json, "
    "external.txt, sources/...).\n"
    "2. Files named in external.txt (Word, PDF, images...): copy them into {1}/sources/ from a connected "
    "folder (.active-memory/packs/{0}/sources/), the Project's uploaded files, or an attached pack-{0}.zip. "
    "If one cannot be found, say so; the work can still continue from the handoff.\n"
    "3. If the Project has nothing, use a connected folder (.active-memory/packs/{0}/) or an attached "
    "pack-{0}.zip (unzip into {1}).\n"
    "Then run with Bash: {2} verify \"{1}\" and report its result line. Pinned rules in rules.json "
    "are restored automatically from your next message."
)
MAX_RULES = 15
RULE_CHARS = 200
RULES_RE = re.compile(r"^\s*/(?:active-memory:)?amrules\b(.*)$", re.IGNORECASE | re.DOTALL)


def rules_command(prompt, rules):
    """Apply /amrules [add|remove N|clear] and return a note for Claude, or None."""
    m = RULES_RE.match(prompt or "")
    if not m:
        return None
    arg = m.group(1).strip()
    low = arg.lower()
    if low in ("", "list", "show"):
        what = "The user asked to see the pinned rules. Show them as a numbered list"
    elif low in ("clear", "off", "remove all"):
        del rules[:]
        what = "All pinned rules were removed. Confirm in one line"
    elif re.match(r"^(remove|delete|rm)\s+\d+$", low):
        n = int(low.split()[1])
        if 1 <= n <= len(rules):
            gone = rules.pop(n - 1)
            what = "Rule %d was removed (\"%s\"). Confirm and show the remaining list" % (n, gone)
        else:
            what = "There is no rule %d. Show the list" % n
    else:
        text = re.sub(r"^add\s+", "", arg, flags=re.IGNORECASE).strip().strip(u"\"'“”")[:RULE_CHARS]
        if len(rules) >= MAX_RULES:
            what = "The list is full (%d rules). Ask the user which rule to remove first" % MAX_RULES
        elif text and text not in rules:
            rules.append(text)
            what = "Rule %d was pinned. Confirm in one line and show the list" % len(rules)
        else:
            what = "That rule is already pinned. Show the list"
    return "[active-memory] /amrules: %s. Pinned rules are re-sent with every message, so keep the list short." % what


def rules_note(rules):
    return ("[active-memory] Pinned rules for this chat. Follow every one in this reply, even if earlier "
            "messages say otherwise:\n" + "\n".join("%d. %s" % (i + 1, r) for i, r in enumerate(rules)))


def restore_rules(st):
    """After /amload, pick up the pack's pinned rules once they are on disk."""
    where = st.get("load_dir")
    if st.get("rules") or not where:
        return
    path = os.path.join(where, "rules.json")
    if os.path.isfile(path):
        try:
            st["rules"] = [r for r in json.loads(pack_tools.read_text(path) or "[]") if r][:MAX_RULES]
        except ValueError:
            pass
        st.pop("load_dir", None)

CODEWORD_RE = re.compile(r"^\s*/(?:active-memory:)?amcodeword\b(.*)$", re.IGNORECASE | re.DOTALL)


def finalize_capture(fn, *args):
    from finalize_pack import capture
    return capture(fn, *args)


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

    notes = []
    rules = st.setdefault("rules", [])
    rnote = rules_command(prompt, rules)
    if rnote:
        notes.append(rnote)
    sm = re.match(r"^\s*/(?:active-memory:)?amsave\b\s*#?(\d+)?", prompt or "", re.IGNORECASE)
    if sm:
        ids = state.pack_ids()
        target = int(sm.group(1)) if sm.group(1) else None
        cloud = state.is_cloud()
        if target is not None and target not in ids and not cloud:
            listing = "\n".join("- {0}: {1}".format(i, state.pack_title(i)) for i in reversed(ids[-10:]))
            notes.append("[active-memory] Pack {0} does not exist. Ask the user whether to save as a new pack "
                         "instead. Saved packs:\n{1}".format(target, listing or "(none yet)"))
        else:
            updating = target is not None and target in ids
            pack_id = target if target is not None else ((ids[-1] + 1) if ids else 1)
            folder = os.path.join(state.packs_dir(), str(pack_id))
            for sub in ("sources", "history"):
                try:
                    os.makedirs(os.path.join(folder, sub))
                except OSError:
                    pass
            session_no = state.next_session_no(folder)
            src = data.get("transcript_path")
            if src and os.path.isfile(src):
                shutil.copyfile(src, os.path.join(folder, "transcript-{0}.jsonl".format(session_no)))
            staging = os.path.join(data.get("cwd") or os.getcwd(), ".active-memory", "staging-{0}".format(pack_id))
            try:
                os.makedirs(staging)
            except OSError:
                pass
            if updating and os.path.isfile(os.path.join(folder, "handoff.md")):
                shutil.copyfile(os.path.join(folder, "handoff.md"), os.path.join(staging, "previous-handoff.md"))
            if rules:
                io.open(os.path.join(folder, "rules.json"), "w", encoding="utf-8").write(
                    json.dumps(rules, ensure_ascii=False, indent=1) if sys.version_info[0] > 2
                    else json.dumps(rules, ensure_ascii=False, indent=1).decode("utf-8"))
                steps_rules = ("\nPinned rules (copy each word for word into section 4): " + "; ".join(rules))
            else:
                steps_rules = ""
            _, collected = finalize_capture(pack_tools.collect, folder, pack_tools.transcripts(folder),
                                            state.cloud_extra_dirs())
            st["pending_pack"] = {"id": pack_id, "folder": folder, "staging": staging, "tries": 0,
                                 "updating": target is not None}
            steps = RUN_STEPS.format(collected=collected.replace("collect: ", "")[:600], staging=staging) + steps_rules
            cloud_note = ""
            if cloud:
                cloud_note = CLOUD_SAVE.format(pick=(
                    "this updates pack {0}: first copy pack {0}'s handoff.md from the Project "
                    "(active-memory/packs/{0}/) or connected folder into the staging folder as "
                    "previous-handoff.md and build on it (chained handoff).".format(target) if target is not None else
                    "the real one is picked when you store it."))
            if updating:
                old = os.path.join(folder, "handoff.md")
                archived = os.path.join(folder, "history", "handoff-{0}.md".format(session_no - 1))
                if os.path.isfile(old) and not os.path.isfile(archived):
                    shutil.copyfile(old, archived)
                notes.append((
                    "[active-memory] Updating pack {0} at: {1}\nThis is session {2} of this pack. "
                    "The previous handoff is copied to previous-handoff.md in the staging folder. Build the new "
                    "handoff.md FROM it (chained handoff): keep everything that still matters, add "
                    "this chat, bump the Handoff number, add a Lineage line. Add new and changed files to "
                    "sources/ and MANIFEST.md without removing earlier ones. transcript-{2}.jsonl is "
                    "already saved.\n").format(pack_id, folder, session_no, session_no - 1) + steps + cloud_note +
                    "\nTell the user: /amload {0}".format(pack_id))
            else:
                notes.append((
                    "[active-memory] Pack ID {0} is reserved at: {1}\n"
                    "transcript-1.jsonl is already there.\n").format(pack_id, folder) + steps + cloud_note +
                    ("" if cloud else "\nTell the user: /amload {0}".format(pack_id)))
    m = re.match(r"^\s*/(?:active-memory:)?amload\b\s*#?(\d+)?", prompt or "", re.IGNORECASE)
    if m:
        ids = state.pack_ids()
        if m.group(1) and int(m.group(1)) in ids:
            folder = os.path.join(state.packs_dir(), m.group(1))
            _, result = finalize_capture(pack_tools.verify, folder)
            local = os.path.join(data.get("cwd") or os.getcwd(), ".active-memory", "pack-" + m.group(1))
            shutil.rmtree(local, True)
            shutil.copytree(folder, local)
            st["load_dir"] = local
            st["rules"] = []
            notes.append("[active-memory] Pack {0} is loaded into this project at: {1}\n"
                         "(stored copy: {2})\nPlugin check: {3}\nRead handoff.md from the project copy. "
                         "Report this check result to the user in your first line.".format(m.group(1), local, folder, result))
        elif m.group(1) and state.is_cloud():
            local = os.path.join(data.get("cwd") or os.getcwd(), ".active-memory", "pack-" + m.group(1))
            tools = '"{0}" "{1}"'.format(sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pack_tools.py"))
            notes.append(CLOUD_LOAD.format(m.group(1), local, tools))
            st["load_dir"] = local
            st["rules"] = []
        else:
            listing = "\n".join("- {0}: {1}".format(i, state.pack_title(i)) for i in reversed(ids[-10:]))
            notes.append("[active-memory] {0}Saved packs on this computer (newest first):\n{1}".format(
                "Pack {0} was not found. ".format(m.group(1)) if m.group(1) else "",
                listing or "(none yet)"))

    restore_rules(st)
    if st.get("rules"):
        notes.append(rules_note(st["rules"]))
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
        notes.append(note)
    if notes:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(notes),
            }
        }))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # never break the user's chat
        pass
    sys.exit(0)
