#!/usr/bin/env python3
"""Run: python3 tests/test_hooks.py"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "hooks", "scripts")
TMP = tempfile.mkdtemp()
ENV = dict(os.environ, ACTIVE_MEMORY_STATE_DIR=os.path.join(TMP, "state"), ACTIVE_MEMORY_CLOUD="0")
failures = 0


def run(script, payload):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)],
                       input=json.dumps(payload), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def check(name, cond):
    global failures
    print(("PASS " if cond else "FAIL ") + name)
    failures += 0 if cond else 1


def transcript(session, entries):
    path = os.path.join(TMP, session + ".jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return path


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def asst(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def text(t):
    return {"type": "text", "text": t}


def tool_use():
    return {"type": "tool_use", "id": "t1", "name": "Read", "input": {}}


def tool_result():
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def prompt(session, p):
    return run("on_prompt.py", {"session_id": session, "prompt": p, "hook_event_name": "UserPromptSubmit"})


def stop(session, entries, last=None):
    if last is None:  # default: last text in the transcript, like Claude Code sends
        texts = [b["text"] for e in entries if e["type"] == "assistant" for b in e["message"]["content"]
                 if b.get("type") == "text"]
        last = texts[-1] if texts else ""
    return run("check_codeword.py", {"session_id": session, "transcript_path": transcript(session, entries),
                                     "stop_hook_active": False, "last_assistant_message": last})


def state_of(session):
    with open(os.path.join(ENV["ACTIVE_MEMORY_STATE_DIR"], session + ".json")) as f:
        return json.load(f)


# --- codeword parsing ---
prompt("s1", "/amcodeword")
check("default phrase is Yes Boss!", state_of("s1")["codeword"] == "Yes Boss!")
prompt("s1", '/amcodeword "Hey chief!"')
check("custom quoted phrase", state_of("s1")["codeword"] == "Hey chief!")
prompt("s1", "/active-memory:amcodeword Aye captain")
check("namespaced command + unquoted phrase", state_of("s1")["codeword"] == "Aye captain")
prompt("s1", "/amcodeword status")
check("status does not change phrase", state_of("s1")["codeword"] == "Aye captain")
prompt("s1", "/amcodeword OFF")
check("off clears phrase", state_of("s1")["codeword"] is None)
prompt("s1", "please don't /amcodeword this")
check("mid-sentence mention is ignored", state_of("s1")["codeword"] is None)

# --- no phrase leaks to Claude ---
out = prompt("s2", "/amcodeword")
check("setting code word outputs nothing to Claude", out == "")

# --- turn nudges ---
outs = [prompt("s3", f"message {i}") for i in range(1, 37)]
check("no note before 20", all(o == "" for o in outs[:19]))
n20 = json.loads(outs[19])["hookSpecificOutput"]["additionalContext"]
check("note at 20 says yellow", "20 exchanges" in n20 and "yellow" in n20)
n35 = json.loads(outs[34])["hookSpecificOutput"]["additionalContext"]
check("note at 35 says red", "35 exchanges" in n35 and "red" in n35)
check("no note at 21-34 or 36", all(o == "" for o in outs[20:34] + outs[35:]))
check("notes never mention a code word", "Yes Boss" not in n20 + n35)

# --- stop hook ---
prompt("s4", "/amcodeword")
check("reply with code word: silent",
      stop("s4", [user("/amcodeword"), asst(text("Yes Boss! Code word is on."))]) == "")
check("bold code word counts",
      stop("s4", [user("hi"), asst(text("**Yes Boss!** hello"))]) == "")
miss = stop("s4", [user("hi"), asst(text("Yes Boss! old")), user("next question"), asst(text("Sure, here it is."))])
check("missing code word: warns user", "missing your code word" in miss)
check("warning is a systemMessage without the phrase",
      "systemMessage" in json.loads(miss) and "Yes Boss" not in miss)
check("miss counted", state_of("s4")["misses"] == 1)
check("tool turns: first text after the real prompt is judged",
      stop("s4", [user("do it"), asst(tool_use()), tool_result(), asst(text("Yes Boss! Done."))]) == "")
check("tool turns: missing phrase still caught",
      "missing" in stop("s4", [user("do it"), asst(text("Let me look.")), asst(tool_use()), tool_result(),
                                asst(text("Yes Boss! Done."))]))
check("meta (skill) messages are not treated as the prompt",
      stop("s4", [user("/amcheckpoint"), asst(text("Yes Boss! 📌 checkpoint")),
                  dict(user("skill body text"), isMeta=True)]) == "")
check("stop_hook_active: silent",
      run("check_codeword.py", {"session_id": "s4", "transcript_path": transcript("x", [user("a"), asst(text("no"))]),
                                "stop_hook_active": True}) == "")
stale = [user("q1"), asst(text("Yes Boss! answer one"))]
check("stale transcript + missing phrase in last_assistant_message: caught",
      "missing" in stop("s4", stale, last="📌 **Chat checkpoint: Yellow**"))
check("stale transcript + phrase present: silent", stop("s4", stale, last="Yes Boss! answer two") == "")
check("no transcript, only last_assistant_message: caught",
      "missing" in run("check_codeword.py", {"session_id": "s4", "last_assistant_message": "Hello there"}))
prompt("s5", "hello")
check("no code word set: silent", stop("s5", [user("hello"), asst(text("Hi"))]) == "")
check("broken input: exits cleanly",
      subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_codeword.py")], input="not json",
                     capture_output=True, text=True, env=ENV).returncode == 0)

# --- the exact commands from hooks.json, run through a shell ---
import json as _json
_cfg = _json.load(io.open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8"))


def shell_hook(event, payload):
    cmd = _cfg["hooks"][event][0]["hooks"][0]["command"].replace("${CLAUDE_PLUGIN_ROOT}", ROOT)
    p = subprocess.run(cmd, shell=True, input=json.dumps(payload), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout.strip()


code, _ = shell_hook("UserPromptSubmit", {"session_id": "sh1", "prompt": "/amcodeword Aye Captain!"})
check("hooks.json UserPromptSubmit command runs", code == 0 and state_of("sh1")["codeword"] == "Aye Captain!")
code, out = shell_hook("Stop", {"session_id": "sh1", "last_assistant_message": "Hello there"})
check("hooks.json Stop command runs and catches a miss", code == 0 and "missing your code word" in out)
noexe = dict(ENV, PATH="/nonexistent")
p = subprocess.run(_cfg["hooks"]["Stop"][0]["hooks"][0]["command"].replace("${CLAUDE_PLUGIN_ROOT}", ROOT),
                   shell=True, input="{}", capture_output=True, text=True, env=noexe)
check("no interpreter anywhere: still exits 0, prints nothing", p.returncode == 0 and p.stdout.strip() == "")

# --- v0.3.0: /amsave reserves numbered packs, /amload finds them, PreCompact backup ---
ENV["ACTIVE_MEMORY_PACKS_DIR"] = os.path.join(TMP, "packs")
packs = ENV["ACTIVE_MEMORY_PACKS_DIR"]
tx = transcript("save", [user("hello"), asst(text("hi"))])
o1 = json.loads(run("on_prompt.py", {"session_id": "p1", "prompt": "/amsave", "transcript_path": tx, "cwd": os.path.join(TMP, "proj2")}))
c1 = o1["hookSpecificOutput"]["additionalContext"]
check("/amsave reserves pack 1", "Pack ID 1" in c1 and os.path.isdir(os.path.join(packs, "1", "sources")))
check("/amsave copies the transcript into the pack", os.path.isfile(os.path.join(packs, "1", "transcript-1.jsonl")))
o2 = json.loads(run("on_prompt.py", {"session_id": "p2", "prompt": "/active-memory:amsave", "transcript_path": tx, "cwd": os.path.join(TMP, "proj2")}))
check("next /amsave gets pack 2", "Pack ID 2" in o2["hookSpecificOutput"]["additionalContext"])
io.open(os.path.join(packs, "1", "handoff.md"), "w", encoding="utf-8").write(u"# active-memory handoff: Booking page\n")
lcwd = os.path.join(TMP, "loadproj"); os.makedirs(lcwd)
l1 = json.loads(run("on_prompt.py", {"session_id": "p3", "prompt": "/amload 1", "cwd": lcwd}))["hookSpecificOutput"]["additionalContext"]
check("/amload 1 copies the pack into the project and gives the check result",
      "loaded into this project" in l1 and "Plugin check: verify:" in l1 and
      os.path.isfile(os.path.join(lcwd, ".active-memory", "pack-1", "handoff.md")))
l0 = json.loads(run("on_prompt.py", {"session_id": "p4", "prompt": "/amload"}))["hookSpecificOutput"]["additionalContext"]
check("/amload alone lists packs newest first with titles", l0.index("- 2:") < l0.index("- 1: Booking page"))
l9 = json.loads(run("on_prompt.py", {"session_id": "p5", "prompt": "/amload 9"}))["hookSpecificOutput"]["additionalContext"]
check("/amload with a missing ID says not found and lists packs", "Pack 9 was not found" in l9 and "- 1:" in l9)
o3 = json.loads(run("on_prompt.py", {"session_id": "p7", "prompt": "/amsave 1", "transcript_path": tx, "cwd": os.path.join(TMP, "proj2")}))
c3 = o3["hookSpecificOutput"]["additionalContext"]
check("/amsave 1 updates pack 1 as session 2", "Updating pack 1" in c3 and "session 2" in c3)
check("update keeps the first transcript and adds a second",
      os.path.isfile(os.path.join(packs, "1", "transcript-1.jsonl")) and os.path.isfile(os.path.join(packs, "1", "transcript-2.jsonl")))
check("update archives the previous handoff", os.path.isfile(os.path.join(packs, "1", "history", "handoff-1.md")))
check("update does not create a new pack", sorted(os.listdir(packs)) == ["1", "2"])
o4 = json.loads(run("on_prompt.py", {"session_id": "p8", "prompt": "/amsave 1", "transcript_path": tx, "cwd": os.path.join(TMP, "proj2")}))
check("third save of the same pack is session 3", "session 3" in o4["hookSpecificOutput"]["additionalContext"])
o5 = json.loads(run("on_prompt.py", {"session_id": "p9", "prompt": "/amsave 42", "transcript_path": tx, "cwd": os.path.join(TMP, "proj2")}))
check("/amsave with an unknown ID does not create it", "does not exist" in o5["hookSpecificOutput"]["additionalContext"]
      and not os.path.exists(os.path.join(packs, "42")))
check("mid-sentence /amsave is ignored", run("on_prompt.py", {"session_id": "p6", "prompt": "how does /amsave work?"}) == "")
run("pre_compact.py", {"transcript_path": tx})
tdir = os.path.join(TMP, "transcripts")
check("PreCompact saves the transcript", os.path.isdir(tdir) and len(os.listdir(tdir)) == 1)
code, _ = shell_hook("PreCompact", {"transcript_path": tx})
check("hooks.json PreCompact command runs", code == 0)

# --- pack tools: collect, recall, verify ---
import base64 as _b64
TOOLS = [sys.executable, os.path.join(SCRIPTS, "pack_tools.py")]
pk = os.path.join(TMP, "toolpack"); os.makedirs(pk)
work = os.path.join(TMP, "work"); os.makedirs(work)
io.open(os.path.join(work, "booking.html"), "w", encoding="utf-8").write(u"<h1>booking</h1>")
io.open(os.path.join(work, "notes.md"), "w", encoding="utf-8").write(u"notes")
png = _b64.b64encode(b"\x89PNG fake image").decode("ascii")
tl = os.path.join(pk, "transcript-1.jsonl")
with io.open(tl, "w", encoding="utf-8") as f:
    for e in [
        {"type": "user", "message": {"content": [{"type": "text", "text": "Group walk is 1,250 USD, VAT 14%, file booking.html, color #0F766E, rule \"never use red buttons\""},
                                                 {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": png}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "a", "name": "Read", "input": {"file_path": os.path.join(work, "notes.md")}},
                                                      {"type": "tool_use", "id": "b", "name": "Write", "input": {"file_path": os.path.join(work, "booking.html")}},
                                                      {"type": "tool_use", "id": "c", "name": "Read", "input": {"file_path": "/nope/gone.txt"}}]}},
    ]:
        f.write(json.dumps(e) + u"\n")


def tool(*args):
    p = subprocess.run(TOOLS + list(args), capture_output=True, text=True)
    return p.returncode, p.stdout


code, out = tool("collect", pk)
srcs = sorted(os.listdir(os.path.join(pk, "sources")))
check("collect copies read and written files", "booking.html" in srcs and "notes.md" in srcs)
check("collect saves attached images", any(n.startswith("attachment-") and n.endswith(".png") for n in srcs))
check("collect reports files it could not find", "NOT FOUND" in out and "gone.txt" in out)
fps = json.load(io.open(os.path.join(pk, "fingerprints.json"), encoding="utf-8"))
check("collect fingerprints every source", len(fps) == len(srcs) == 3)
tool("collect", pk)
check("collect twice does not duplicate files", len(os.listdir(os.path.join(pk, "sources"))) == 3)

io.open(os.path.join(pk, "handoff.md"), "w", encoding="utf-8").write(u"# active-memory handoff: t\n" + u"\n".join(u"## %d. x" % i for i in range(15)) + u"\nGroup walk 1250 USD\n")
io.open(os.path.join(pk, "MANIFEST.md"), "w", encoding="utf-8").write(u"sources/booking.html")
code, out = tool("recall", pk)
check("recall flags facts missing from the handoff", code == 1 and "14%" in out and "#0F766E" in out and "never use red buttons" in out)
check("recall accepts facts written differently (1,250 vs 1250)", "1,250" not in out)
io.open(os.path.join(pk, "handoff.md"), "a", encoding="utf-8").write(u"VAT 14% · #0F766E · never use red buttons\n")
code, out = tool("recall", pk)
check("recall passes once everything is in", code == 0 and "all" in out)

code, out = tool("verify", pk)
check("verify passes and marks the pack complete", code == 0 and "3 of 3" in out and os.path.isfile(os.path.join(pk, ".complete")))
io.open(os.path.join(pk, "sources", "notes.md"), "w", encoding="utf-8").write(u"tampered")
code, out = tool("verify", pk)
check("verify catches a changed source", code == 1 and "notes.md" in out and not os.path.exists(os.path.join(pk, ".complete")))
io.open(os.path.join(pk, "handoff.md"), "w", encoding="utf-8").write(u"# active-memory handoff: t\n## 0. x\n")
code, out = tool("verify", pk)
check("verify catches missing handoff sections", code == 1 and "## 14." in out)

# --- automatic save finishing (Stop hook), no scripts run by Claude ---
proj3 = os.path.join(TMP, "proj3"); os.makedirs(proj3)
txf = transcript("fin", [user("Group walk is 1,250 USD and VAT is 14%"), asst(text("ok"))])
o = json.loads(run("on_prompt.py", {"session_id": "fin1", "prompt": "/amsave", "transcript_path": txf, "cwd": proj3}))
ctx = o["hookSpecificOutput"]["additionalContext"]
pid = re.search(r"Pack ID (\d+)", ctx).group(1)
stg = os.path.join(proj3, ".active-memory", "staging-" + pid)
check("/amsave creates a staging folder inside the project", os.path.isdir(stg) and stg in ctx)
check("/amsave tells Claude not to run scripts", "Do NOT run any scripts" in ctx)
fin = lambda: run("finalize_pack.py", {"session_id": "fin1"})
out = json.loads(fin())
check("finishing without a handoff sends Claude back", out.get("decision") == "block" and stg in out["reason"])
hand = u"# active-memory handoff: t\n" + u"\n".join(u"## %d. x" % i for i in range(15)) + u"\nGroup walk 1,250 USD\n"
io.open(os.path.join(stg, "handoff.md"), "w", encoding="utf-8").write(hand)
io.open(os.path.join(stg, "MANIFEST.md"), "w", encoding="utf-8").write(u"none")
out = json.loads(fin())
check("recall miss sends Claude back with the exact fact", out.get("decision") == "block" and "14%" in out["reason"])
io.open(os.path.join(stg, "handoff.md"), "a", encoding="utf-8").write(u"VAT 14%\n")
out = json.loads(fin())
check("complete save is verified and reported to the user", "verified" in out.get("systemMessage", "") and "pack " + pid in out["systemMessage"])
check("staging folder is cleaned up after a good save", not os.path.exists(stg))
check("pack folder has the handoff and the .complete marker",
      os.path.isfile(os.path.join(packs, pid, "handoff.md")) and os.path.isfile(os.path.join(packs, pid, ".complete")))
check("finish hook is silent when no save is pending", fin() == "")
txl = transcript("long", [user("short chat"), asst(text("ok"))])
o = json.loads(run("on_prompt.py", {"session_id": "fin2", "prompt": "/amsave", "transcript_path": txl, "cwd": proj3}))
pid2 = re.search(r"Pack ID (\d+)", o["hookSpecificOutput"]["additionalContext"]).group(1)
stg2 = os.path.join(proj3, ".active-memory", "staging-" + pid2)
io.open(os.path.join(stg2, "handoff.md"), "w", encoding="utf-8").write(hand + u"word " * 2000)
out = json.loads(run("finalize_pack.py", {"session_id": "fin2"}))
check("an over-budget handoff is sent back to be shortened", out.get("decision") == "block" and "1600" in out["reason"])
io.open(os.path.join(stg2, "handoff.md"), "w", encoding="utf-8").write(hand)
out = json.loads(run("finalize_pack.py", {"session_id": "fin2"}))
check("a trimmed handoff then saves and reports its word count", "verified" in out.get("systemMessage", "") and "words" in out["systemMessage"])

# --- v0.3.0 fixes from the first real use: chatter, binaries, shell-used files, cloud sessions ---
pk2 = os.path.join(TMP, "pk2"); os.makedirs(pk2)
docx = os.path.join(work, "cv master.docx"); open(docx, "wb").write(b"PK\x03\x04 binary docx")
with io.open(os.path.join(pk2, "transcript-1.jsonl"), "w", encoding="utf-8") as f:
    for e in [
        {"type": "user", "message": {"content": "Are we doing good? \"Continue please where u left off\" [Request interrupted by user] Salary is 4000 USD"}},
        {"type": "user", "message": {"content": "<system-reminder>internal \"do not count this\" 99 EUR</system-reminder> ok"}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "x", "name": "Bash", "input": {"command": 'python3 build.py "%s" /usr/bin/env.py' % docx}}]}},
    ]:
        f.write(json.dumps(e) + u"\n")
tool("collect", pk2)
check("collect copies a binary file used only in a shell command (path with spaces)",
      "cv master.docx" in os.listdir(os.path.join(pk2, "sources")))
check("collect skips system files", not any(n.startswith("env") for n in os.listdir(os.path.join(pk2, "sources"))))
io.open(os.path.join(pk2, "handoff.md"), "w", encoding="utf-8").write(u"# active-memory handoff: t\nSalary 4000 USD\n")
code, out = tool("recall", pk2)
check("recall ignores chatter, interruptions and system text", code == 0 and "99 EUR" not in out)
io.open(os.path.join(pk2, "handoff.md"), "w", encoding="utf-8").write(u"# active-memory handoff: t\n")
io.open(os.path.join(pk2, "sources", "notes.txt"), "w", encoding="utf-8").write(u"expected salary 4000 USD")
code, out = tool("recall", pk2)
check("a fact kept in a saved source counts as kept (no handoff bloat)", code == 0)

CENV = dict(ENV, ACTIVE_MEMORY_CLOUD="1", ACTIVE_MEMORY_PACKS_DIR=os.path.join(TMP, "cloudpacks"))
def crun(script, payload):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)], input=json.dumps(payload),
                       capture_output=True, text=True, env=CENV)
    return p.stdout.strip()
cp = os.path.join(TMP, "cloudproj"); os.makedirs(cp)
c = json.loads(crun("on_prompt.py", {"session_id": "c1", "prompt": "/amsave", "transcript_path": tx, "cwd": cp}))["hookSpecificOutput"]["additionalContext"]
check("cloud /amsave says the computer is temporary and the number is a working number",
      "Cloud session" in c and "working number" in c and "Tell the user: /amload" not in c)
c = json.loads(crun("on_prompt.py", {"session_id": "c2", "prompt": "/amsave 5", "transcript_path": tx, "cwd": cp}))["hookSpecificOutput"]["additionalContext"]
check("cloud /amsave 5 fetches pack 5 from storage instead of refusing", "does not exist" not in c and "updates pack 5" in c and "previous-handoff.md" in c)
c = json.loads(crun("on_prompt.py", {"session_id": "c3", "prompt": "/amload 8", "cwd": cp}))["hookSpecificOutput"]["additionalContext"]
check("cloud /amload 8 (not on this computer) looks in the connected folder and Project", "not on this temporary computer" in c and "verify" in c)
check("cloud /amload 8 looks in the Project first, then folder or zip",
      c.index("The Project") < c.index("connected folder") and "external.txt" in c)

# --- v0.3.0: cloud saves go to the Project ---
cst = os.path.join(cp, ".active-memory", "staging-1")
c1 = json.loads(crun("on_prompt.py", {"session_id": "c9", "prompt": "/amsave", "transcript_path": tx, "cwd": cp}))
cst = re.search(r"into this folder inside the project: (\S+)", c1["hookSpecificOutput"]["additionalContext"]).group(1)
io.open(os.path.join(cst, "handoff.md"), "w", encoding="utf-8").write(hand)
io.open(os.path.join(cst, "MANIFEST.md"), "w", encoding="utf-8").write(u"none")
out = {}
for _ in range(4):
    out = json.loads(crun("finalize_pack.py", {"session_id": "c9"}) or "{}")
    if "verified" in out.get("systemMessage", ""):
        break
    io.open(os.path.join(cst, "handoff.md"), "a", encoding="utf-8").write(out.get("reason", "") + u"\n")
check("cloud save, once verified, tells Claude to store it in the Project",
      out.get("decision") == "block" and "project_write" in out.get("reason", "") and "external.txt" in out["reason"])
proj_out = re.search(r"every file in (\S+) with project_write", out["reason"]).group(1)
check("cloud save prepares a Project-sized bundle", os.path.isfile(os.path.join(proj_out, "handoff.md")))
check("finish hook is quiet after the Project instruction", crun("finalize_pack.py", {"session_id": "c9"}) == "")

# --- bundle: text goes to the Project, binaries are listed ---
bp = os.path.join(TMP, "bp"); os.makedirs(os.path.join(bp, "sources"))
io.open(os.path.join(bp, "handoff.md"), "w", encoding="utf-8").write(hand)
io.open(os.path.join(bp, "sources", "notes.md"), "w", encoding="utf-8").write(u"plain text")
open(os.path.join(bp, "sources", "cv.docx"), "wb").write(b"PK\x03\x04\x00\x00binary")
import hashlib
fp = lambda n: hashlib.sha256(open(os.path.join(bp, "sources", n), "rb").read()).hexdigest()
io.open(os.path.join(bp, "fingerprints.json"), "w", encoding="utf-8").write(json.dumps({"notes.md": {"sha256": fp("notes.md")}, "cv.docx": {"sha256": fp("cv.docx")}}))
bo = os.path.join(TMP, "bo")
code, out = tool("bundle", bp, bo)
check("bundle keeps text sources and lists binaries in external.txt",
      os.path.isfile(os.path.join(bo, "sources", "notes.md")) and not os.path.exists(os.path.join(bo, "sources", "cv.docx"))
      and "cv.docx" in io.open(os.path.join(bo, "external.txt"), encoding="utf-8").read())
code, out = tool("verify", bo)
check("a pack loaded from a Project verifies, naming files stored elsewhere", code == 0 and "1 of 2" in out and "cv.docx" in out)

# --- /amrules: pinned rules re-sent every message ---
rs = "rules1"
o = run("on_prompt.py", {"session_id": rs, "prompt": "/amrules prices always in USD with two decimals"})
c = json.loads(o)["hookSpecificOutput"]["additionalContext"]
check("/amrules <text> pins a rule", "Rule 1 was pinned" in c and "1. prices always in USD" in c)
run("on_prompt.py", {"session_id": rs, "prompt": "/amrules add never use red"})
c = json.loads(run("on_prompt.py", {"session_id": rs, "prompt": "make the button"}))["hookSpecificOutput"]["additionalContext"]
check("pinned rules are sent with every normal message", "Pinned rules" in c and "2. never use red" in c)
c = json.loads(run("on_prompt.py", {"session_id": rs, "prompt": "/amrules remove 1"}))["hookSpecificOutput"]["additionalContext"]
check("/amrules remove N removes that rule", "Rule 1 was removed" in c and "1. never use red" in c and "two decimals" not in c.split("Pinned rules")[1])
txr = transcript("rules", [user("hello"), asst(text("ok"))])
pr = os.path.join(TMP, "projr"); os.makedirs(pr)
c = json.loads(run("on_prompt.py", {"session_id": rs, "prompt": "/amsave", "transcript_path": txr, "cwd": pr}))["hookSpecificOutput"]["additionalContext"]
rid = re.search(r"Pack ID (\d+)", c).group(1)
check("/amsave stores pinned rules in the pack and asks for them in section 4",
      os.path.isfile(os.path.join(packs, rid, "rules.json")) and "never use red" in c.split("Pinned rules (copy")[1])
io.open(os.path.join(packs, rid, "handoff.md"), "w", encoding="utf-8").write(hand)
code, out = tool("recall", os.path.join(packs, rid))
check("recall flags a pinned rule missing from the handoff", code == 1 and "pinned rule" in out and "never use red" in out)
c = json.loads(run("on_prompt.py", {"session_id": "rules2", "prompt": "/amload " + rid, "cwd": pr}))["hookSpecificOutput"]["additionalContext"]
c = json.loads(run("on_prompt.py", {"session_id": "rules2", "prompt": "next"}))["hookSpecificOutput"]["additionalContext"]
check("/amload brings the pinned rules into the new chat", "Pinned rules" in c and "never use red" in c)
c = json.loads(run("on_prompt.py", {"session_id": rs, "prompt": "/amrules clear"}))["hookSpecificOutput"]["additionalContext"]
o = run("on_prompt.py", {"session_id": rs, "prompt": "hi"})
check("/amrules clear stops sending rules", "removed" in c and "Pinned rules" not in o)

print(f"\n{failures} failure(s)")
sys.exit(1 if failures else 0)
