#!/usr/bin/env python3
"""Run: python3 tests/test_hooks.py"""
import io
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "hooks", "scripts")
TMP = tempfile.mkdtemp()
ENV = dict(os.environ, ACTIVE_MEMORY_STATE_DIR=os.path.join(TMP, "state"))
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

print(f"\n{failures} failure(s)")
sys.exit(1 if failures else 0)
