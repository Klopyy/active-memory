#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stop hook (any Python 2.7 or 3.x): finishes an /amsave without permission prompts.

After Claude writes handoff.md and MANIFEST.md into the project's staging folder, this
copies them into the pack, runs recall and verify, and if facts are missing sends Claude
back (decision: block) with the exact list, up to two times.
"""
import io
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402
import pack_tools  # noqa: E402

MAX_FIXES = 3
CLOUD_STORE = (
    "active-memory: pack {id} is verified, but this cloud computer is temporary. Store it now so any new "
    "chat can load it ({bundled}):\n"
    "1. Pack number: if this updates an existing pack ({update}) keep {id}. Otherwise use the Projects tool "
    "(project_info) and take one more than the highest number under active-memory/packs/ (1 if none).\n"
    "2. If the Projects tool is available: upload every file in {out} with project_write "
    "(local_path = the file, path = active-memory/packs/<number>/<path inside {out}>). Keep the same layout.\n"
    "3. Files listed in {out}/external.txt (Word, PDF, images, big files) cannot go in a Project. If a folder "
    "on the user's computer is connected, copy the whole pack {folder} to <that folder>/.active-memory/packs/<number>/ "
    "(device_commit_files). If not, zip {folder} as pack-<number>.zip and send it to the user. If the "
    "Projects tool is missing, do this for the whole pack.\n"
    "4. Tell the user in at most 3 lines: the number, where it is stored, and \"In a new chat in this "
    "Project, type /amload <number>\". Do not repeat the pack contents."
)
WORD_LIMIT = 1600


def capture(fn, *args):
    out = io.StringIO() if sys.version_info[0] > 2 else io.BytesIO()
    old = sys.stdout
    sys.stdout = out
    try:
        code = fn(*args)
    finally:
        sys.stdout = old
    text = out.getvalue()
    if not isinstance(text, type(u"")):
        text = text.decode("utf-8")
    return code, text.strip()


def main():
    data = state.read_stdin_json(sys.stdin)
    session = data.get("session_id", "unknown")
    st = state.load(session)
    job = st.get("pending_pack")
    if not job:
        return
    staging, folder = job["staging"], job["folder"]
    if not os.path.isfile(os.path.join(staging, "handoff.md")):
        if job.get("tries", 0) >= MAX_FIXES:
            st.pop("pending_pack", None); state.save(session, st)
            print(json.dumps({"systemMessage": "⚠️ active-memory: pack %s was not saved (no handoff was written)." % job["id"]}))
            return
        job["tries"] = job.get("tries", 0) + 1; state.save(session, st)
        print(json.dumps({"decision": "block", "reason": "active-memory: write handoff.md and MANIFEST.md into %s to finish saving pack %s." % (staging, job["id"])}))
        return
    for name in ("handoff.md", "MANIFEST.md"):
        src = os.path.join(staging, name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(folder, name))
    code, recall_out = capture(pack_tools.recall, folder)
    if code != 0 and job.get("tries", 0) < MAX_FIXES:
        job["tries"] = job.get("tries", 0) + 1; state.save(session, st)
        lines = recall_out.splitlines()
        short = "\n".join(lines[:41]) + ("\n…and %d more" % (len(lines) - 41) if len(lines) > 41 else "")
        print(json.dumps({"decision": "block", "reason":
              "active-memory recall check for pack %s:\n%s\nEdit %s/handoff.md to include each, or put it in section 7 if it was replaced. Keep it compact." % (job["id"], short, staging)}))
        return
    words = len(pack_tools.read_text(os.path.join(folder, "handoff.md")).split())
    if code == 0 and words > WORD_LIMIT and job.get("tries", 0) < MAX_FIXES:
        job["tries"] = job.get("tries", 0) + 1; state.save(session, st)
        print(json.dumps({"decision": "block", "reason":
              "active-memory: %s/handoff.md is %d words; the budget is %d so the next chat starts light. "
              "Shorten discussion, narration and repeated lines. Never remove a rule, correction, decision, "
              "exact value, or anything section 14 needs; refer to sources by path instead of quoting them."
              % (staging, words, WORD_LIMIT)}))
        return
    vcode, verify_out = capture(pack_tools.verify, folder)
    st.pop("pending_pack", None); state.save(session, st)
    if vcode == 0:
        shutil.rmtree(staging, True)
        note = "✅ active-memory: pack %s saved and verified. %s Handoff: %d words." % (
            job["id"], verify_out.replace("verify: ", ""), words)
        if code != 0:
            note += " (recall still lists some facts; they are in the transcript)"
        if state.is_cloud():
            out = os.path.join(os.path.dirname(staging), "project-%s" % job["id"])
            _, bundled = capture(pack_tools.bundle, folder, out)
            print(json.dumps({"systemMessage": note, "decision": "block", "reason": CLOUD_STORE.format(
                id=job["id"], out=out, folder=folder, bundled=bundled, update=job.get("updating", False))}))
            return
    else:
        note = "⚠️ active-memory: pack %s saved but did not verify:\n%s" % (job["id"], verify_out)
    print(json.dumps({"systemMessage": note}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
