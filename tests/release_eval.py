#!/usr/bin/env python3
"""Release gate: run a real 24-message chat through Claude Code with this plugin,
save it with /amsave, load it in a fresh session with /amload, and check that all
28 planted details survived. Release only if this prints 28/28 and PASS.

Needs the `claude` CLI, logged in. Uses real tokens (about 10 minutes).
Run:  python3 tests/release_eval.py
"""
import json, os, re, subprocess, sys, tempfile, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = tempfile.mkdtemp(prefix="am-eval-")
ENV = dict(os.environ, ACTIVE_MEMORY_PACKS_DIR=os.path.join(WORK, "packs"),
           ACTIVE_MEMORY_STATE_DIR=os.path.join(WORK, "state"), ACTIVE_MEMORY_CLOUD="0")

TURNS = [
    "/amcodeword",
    "Hi. We're planning (not coding yet, don't write any code until I say) a booking page for Sunny Paws, a small made-up dog-walking business. Rule: all page text must be in Spanish, but prices always show in USD with two decimals. Keep your replies short and no emojis please.",
    "Prices: a walk is $18.00 per dog per 30 minutes, with a minimum of 30 minutes. Overnight dog sitting is $95.00 per night. Sales tax is 8% on everything.",
    "Priya is the owner and approves all prices, and Leo will use the page daily to take bookings.",
    "Suggest a layout for the price summary table.",
    "Correction: the Price column must be on the RIGHT side of the table, not the left, so totals line up.",
    "Name the file booking.html for now.",
    "Buttons: never use red for any button. Use teal #0F766E for primary buttons.",
    "Should we add a PDF export button? Give me pros and cons in 3 lines.",
    "Forget the PDF export idea, too heavy. We'll just use the browser's print-to-PDF instead.",
    "Weekend surcharge for walks on Saturday and Sunday is 10%.",
    "Nail trimming is a flat $12.00 per dog.",
    "Actually rename the file to sunny-paws-booking.html, booking.html is too generic.",
    "The admin password for the settings panel will be Paws#2026, remember that.",
    "Should the page save quotes? Short answer.",
    "No saving for now. Later maybe.",
    "Walks longer than 90 minutes need manual approval from Priya, the page should just show a warning in that case instead of a price.",
    "Fonts: use Inter for all text.",
    "I think the weekend surcharge might be 15% now, not sure, I need to check with Priya.",
    "Summarize the overnight price formula in one line.",
    "Correction: overnight stays count both the drop-off day and the pick-up day, so it's inclusive.",
    "Next we will add a grooming section, but I don't have those prices yet.",
    "OK that's enough planning for today.",
    "/amsave",
]

# (name, regex that must appear in handoff.md)
FACTS = [
    ("title line", r"^# active-memory handoff"), ("15 sections", r"## 14\."),
    ("Spanish rule", r"Spanish"), ("two decimals", r"(?i)two decimals|2 decimals"), ("no code yet", r"(?i)no code|not (to )?write (any )?code|until .*say"),
    ("short replies", r"(?i)short"), ("no emojis", r"(?i)emoji"),
    ("walk $18.00", r"18\.00"), ("min 30 minutes", r"\b30\s?(min|minute)"), ("overnight 95", r"\b95\b"), ("tax 8%", r"\b8\s?%"),
    ("nail trim 12", r"\b12\b"), ("90 min approval", r"\b90\b"), ("teal #0F766E", r"(?i)#0F766E"),
    ("no red buttons", r"(?i)\bred\b"), ("Inter font", r"Inter\b"), ("Priya", r"Priya"), ("Leo", r"Leo\b"),
    ("correction: price RIGHT", r"(?i)right"), ("correction: inclusive days", r"(?i)inclusive"),
    ("PDF export rejected", r"(?i)pdf"), ("renamed file", r"sunny-paws-booking\.html"), ("old name kept as changed", r"(?<!sunny-paws-)booking\.html"),
    ("no quote saving", r"(?i)sav"), ("surcharge 10%", r"10\s?%"), ("15% flagged open", r"15\s?%"),
    ("grooming next", r"(?i)grooming"), ("code word carried", r"Yes Boss!"),
]


def claude(args, msg, cwd):
    p = subprocess.run(["claude", "-p", "--plugin-dir", ROOT, "--permission-mode", "acceptEdits"] + args + [msg],
                       capture_output=True, text=True, cwd=cwd, env=ENV, stdin=subprocess.DEVNULL, timeout=600)
    return p.stdout.strip()


def main():
    chat = os.path.join(WORK, "chat"); os.makedirs(chat)
    sid = str(uuid.uuid4())
    for i, msg in enumerate(TURNS):
        claude(["--session-id", sid] if i == 0 else ["--resume", sid], msg, chat)
        print("turn %d/%d" % (i + 1, len(TURNS)), flush=True)
    packs = ENV["ACTIVE_MEMORY_PACKS_DIR"]
    handoff = os.path.join(packs, "1", "handoff.md")
    text = open(handoff, encoding="utf-8").read() if os.path.isfile(handoff) else ""
    hits = [(n, bool(re.search(p, text, re.M))) for n, p in FACTS]
    for n, ok in hits:
        print(("  ok   " if ok else "  MISS ") + n)
    secret_ok = "Paws#2026" not in text
    print(("  ok   " if secret_ok else "  MISS ") + "password removed")
    complete = os.path.isfile(os.path.join(packs, "1", ".complete"))
    print(("  ok   " if complete else "  MISS ") + "pack verified (.complete)")
    load_dir = os.path.join(WORK, "newchat"); os.makedirs(load_dir)
    reply = claude(["--session-id", str(uuid.uuid4())], "/amload 1", load_dir)
    load_ok = reply.startswith("Yes Boss!") and "loaded" in reply.lower()
    print(("  ok   " if load_ok else "  MISS ") + "new chat loads pack 1 with the code word")
    score = sum(ok for _, ok in hits)
    passed = score == len(FACTS) and secret_ok and complete and load_ok
    print("\n%d/%d facts · %s" % (score, len(FACTS), "PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
