#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""active-memory pack tools. Any Python 2.7 or 3.x, no third-party packages.

  pack_tools.py collect  <pack> [--transcript FILE] [--extra DIR ...]
      Copy every file the chat touched (read, written, edited, attached) into
      <pack>/sources/ and write fingerprints to <pack>/fingerprints.json.
  pack_tools.py recall   <pack>
      List facts from the transcripts (numbers, money, file names, URLs, emails,
      colors, quotes) that are missing from handoff.md and MANIFEST.md.
  pack_tools.py verify   <pack>
      Check every fingerprint and the handoff headings. Writes .complete when OK.
  pack_tools.py bundle   <pack> <out>
      Copy what a claude.ai Project can hold (handoff, manifest, fingerprints, pinned
      rules and small text sources) into <out>, and list the rest in external.txt.

Output is short on purpose: only what Claude must act on.
"""
from __future__ import print_function

import base64
import hashlib
import io
import json
import os
import re
import shutil
import sys

HEADINGS = ["## %d." % i for i in range(15)]
FILE_KEYS = ("file_path", "path", "notebook_path", "local_path")
SKIP_PREFIXES = ("/usr/", "/bin/", "/sbin/", "/lib", "/etc/", "/proc/", "/sys/", "/dev/", "/opt/", "/var/lib/")
MAX_BYTES = 25 * 1024 * 1024
PATH_IN_CMD = re.compile(r"""["']((?:/|[A-Za-z]:[\\/])[^"'\n]+?\.[A-Za-z0-9]{1,6})["']|((?:/|[A-Za-z]:[\\/])[^\s"'<>|;&*?]+\.[A-Za-z0-9]{1,6})""")


def worth_copying(path):
    norm = path.replace("\\", "/")
    if any(norm.startswith(p) for p in SKIP_PREFIXES):
        return False
    if "/.claude/plugins/" in norm or "/active-memory/packs/" in norm or "/.active-memory/" in norm:
        return False
    return os.path.isfile(path) and os.path.getsize(path) <= MAX_BYTES


def sha256(path):
    h = hashlib.sha256()
    f = open(path, "rb")
    try:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    finally:
        f.close()
    return h.hexdigest()


def read_text(path):
    try:
        f = io.open(path, encoding="utf-8", errors="replace")
        try:
            return f.read()
        finally:
            f.close()
    except (IOError, OSError):
        return u""


def transcripts(pack):
    names = sorted(n for n in os.listdir(pack) if re.match(r"^transcript(-\d+)?\.jsonl$", n))
    return [os.path.join(pack, n) for n in names]


def entries(path):
    out = []
    for line in read_text(path).splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def blocks(entry):
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [c for c in (content or []) if isinstance(c, dict)]


def safe_name(name, taken):
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", os.path.basename(name)) or "file"
    stem, ext = os.path.splitext(base)
    n, cand = 1, base
    while cand in taken:
        n += 1
        cand = "%s-%d%s" % (stem, n, ext)
    taken.add(cand)
    return cand


def collect(pack, transcript_files, extra_dirs):
    src_dir = os.path.join(pack, "sources")
    if not os.path.isdir(src_dir):
        os.makedirs(src_dir)
    fp_path = os.path.join(pack, "fingerprints.json")
    old = json.loads(read_text(fp_path) or "{}")
    taken = set(os.listdir(src_dir))
    by_origin = dict((v.get("origin"), k) for k, v in old.items())
    found, attachments = [], 0
    for t in transcript_files:
        for e in entries(t):
            for b in blocks(e):
                if b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    for k in FILE_KEYS:
                        if isinstance(inp.get(k), str):
                            found.append(inp[k])
                    cmd = inp.get("command")
                    if isinstance(cmd, str):
                        found.extend(p for p in (m.group(1) or m.group(2) for m in PATH_IN_CMD.finditer(cmd)) if worth_copying(p))
                elif b.get("type") in ("image", "document") and e.get("type") == "user":
                    src = b.get("source") or {}
                    if src.get("type") == "base64" and src.get("data"):
                        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
                               "image/webp": ".webp", "application/pdf": ".pdf"}.get(src.get("media_type"), ".bin")
                        data = base64.b64decode(src["data"])
                        key = "attachment:" + hashlib.sha256(data).hexdigest()[:16]
                        if key in by_origin:
                            continue
                        attachments += 1
                        name = safe_name("attachment-%d%s" % (len(by_origin) + attachments, ext), taken)
                        f = open(os.path.join(src_dir, name), "wb")
                        try:
                            f.write(data)
                        finally:
                            f.close()
                        by_origin[key] = name
    for d in extra_dirs:
        for root, _dirs, files in os.walk(d):
            for n in files:
                found.append(os.path.join(root, n))
    copied, missing = 0, []
    for path in dict.fromkeys(found):  # keeps order, drops duplicates
        if not os.path.isfile(path):
            missing.append(path)
            continue
        if not worth_copying(path):
            continue
        name = by_origin.get(path) or safe_name(path, taken)
        shutil.copyfile(path, os.path.join(src_dir, name))
        by_origin[path] = name
        copied += 1
    fps = {}
    for origin, name in by_origin.items():
        p = os.path.join(src_dir, name)
        if os.path.isfile(p):
            fps[name] = {"origin": origin, "sha256": sha256(p), "bytes": os.path.getsize(p)}
    text = json.dumps(fps, indent=1, ensure_ascii=False, sort_keys=True)
    if not isinstance(text, type(u"")):
        text = text.decode("utf-8")
    f = io.open(fp_path, "w", encoding="utf-8")
    try:
        f.write(text)
    finally:
        f.close()
    print("collect: %d files in sources/ (%d copied now, %d attachments saved)" % (len(fps), copied, attachments))
    for m in missing:
        print("NOT FOUND (list in MANIFEST.md as NOT COPIED): %s" % m)


FACT_PATTERNS = [
    ("money", r"\d[\d,]*(?:\.\d+)?\s?(?:EGP|USD|EUR|GBP|AED|SAR|\$|€|£)|[\$€£]\s?\d[\d,]*(?:\.\d+)?"),
    ("percent", r"\d+(?:\.\d+)?\s?%"),
    ("measure", r"\d+(?:\.\d+)?\s?(?:m|cm|mm|km|kg|t|ton|tons|kW|V|A|Hz|bar|psi|days?|hours?|meters?)\b"),
    ("file", r"\b[\w.-]+\.(?:html?|css|js|ts|py|json|md|txt|csv|xlsx?|docx?|pptx?|pdf|png|jpe?g|zip|plugin|sh|ps1|sql)\b"),
    ("url", r"https?://[^\s)>\]\"']+"),
    ("email", r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    ("color", r"#[0-9A-Fa-f]{6}\b"),
    ("version", r"\bv?\d+\.\d+\.\d+\b"),
    ("quote", r"\"([^\"\n]{4,80})\""),
]
ADVISORY = ("quote",)
NOISE = re.compile(r"<([a-z_-]+)[^>]*>.*?</\1>|\[Request interrupted[^\]]*\]", re.S | re.I)
TEXT_EXT = (".md", ".txt", ".csv", ".json", ".html", ".htm", ".py", ".js", ".css", ".xml", ".yml", ".yaml", ".log")


def norm(s):
    return re.sub(r"[\s,]", "", s.lower())


def recall(pack):
    hay = [read_text(os.path.join(pack, "handoff.md")), read_text(os.path.join(pack, "MANIFEST.md"))]
    src_dir = os.path.join(pack, "sources")
    if os.path.isdir(src_dir):
        for n in os.listdir(src_dir):
            p = os.path.join(src_dir, n)
            if n.lower().endswith(TEXT_EXT) and os.path.getsize(p) <= 2 * 1024 * 1024:
                hay.append(read_text(p))  # a fact kept in a saved source does not need repeating
    haystack = norm(u"".join(hay))
    must, check_only, seen = [], [], set()
    for t in transcripts(pack):
        for e in entries(t):
            if e.get("type") != "user" or e.get("isMeta") or e.get("isCompactSummary"):
                continue  # only what the user typed
            for b in blocks(e):
                if b.get("type") != "text":
                    continue
                text = NOISE.sub(" ", b.get("text") or "")
                for kind, pat in FACT_PATTERNS:
                    for m in re.finditer(pat, text):
                        val = (m.group(1) if m.groups() else m.group(0)).strip().rstrip(".,;:")
                        if kind == "quote" and (val.endswith("?") or len(val.split()) < 3):
                            continue  # questions and short chatter are not rules
                        key = norm(val)
                        if not key or key in seen:
                            continue
                        seen.add(key)
                        if key not in haystack:
                            (check_only if kind in ADVISORY else must).append((kind, val))
    handoff_only = norm(hay[0])
    for rule in json.loads(read_text(os.path.join(pack, "rules.json")) or "[]"):
        key = norm(rule)
        if key and key not in seen:
            seen.add(key)
            if key not in handoff_only:
                must.append(("pinned rule, copy word for word into section 4", rule))
    if not must:
        print("recall: all %d data facts kept" % (len(seen) - len(check_only)) +
              ("; %d quoted phrases not in the handoff (fine unless one is a rule)" % len(check_only) if check_only else ""))
        return 0
    print("recall: %d data facts missing. Add each to the handoff (or section 7 if replaced):" % len(must))
    for kind, val in must:
        print("- [%s] %s" % (kind, val))
    if check_only:
        print("Also check (add only if it is a rule or decision, never chatter): " +
              "; ".join(v for _, v in check_only[:15]))
    return 1


def verify(pack):
    problems = []
    handoff = read_text(os.path.join(pack, "handoff.md"))
    if not handoff.startswith("# active-memory handoff"):
        problems.append("handoff.md missing or has the wrong title line")
    for h in HEADINGS:
        if h not in handoff:
            problems.append("handoff.md is missing heading %s" % h)
    fps = json.loads(read_text(os.path.join(pack, "fingerprints.json")) or "{}")
    ok, elsewhere = 0, []
    ext = external_names(pack)
    for name, info in sorted(fps.items()):
        p = os.path.join(pack, "sources", name)
        if not os.path.isfile(p) and name in ext:
            elsewhere.append(name)
        elif not os.path.isfile(p):
            problems.append("missing source: %s" % name)
        elif sha256(p) != info.get("sha256"):
            problems.append("changed or corrupted source: %s" % name)
        else:
            ok += 1
    marker = os.path.join(pack, ".complete")
    if problems:
        if os.path.exists(marker):
            os.remove(marker)
        print("verify: FAILED")
        for p in problems:
            print("- " + p)
        return 1
    io.open(marker, "w", encoding="utf-8").write(u"ok\n")
    msg = "verify: OK, %d of %d sources match their fingerprints, handoff complete" % (ok, len(fps))
    if elsewhere:
        msg += "; not loaded here (stored elsewhere): " + ", ".join(elsewhere[:20])
    print(msg)
    return 0


TEXT_MAX = 100 * 1024       # one text source kept in a Project
PROJECT_TEXT_MAX = 400 * 1024  # all text sources together, so the Project stays light
META = ("handoff.md", "MANIFEST.md", "fingerprints.json", "rules.json")


def is_text(path):
    try:
        f = open(path, "rb")
        try:
            raw = f.read(TEXT_MAX + 1)
        finally:
            f.close()
        if len(raw) > TEXT_MAX or b"\x00" in raw:
            return False
        raw.decode("utf-8")
        return True
    except (IOError, OSError, UnicodeDecodeError):
        return False


def bundle(pack, out):
    """Project-sized copy of a pack. Binary or large sources are listed, not copied."""
    if os.path.isdir(out):
        shutil.rmtree(out, True)
    os.makedirs(os.path.join(out, "sources"))
    for name in META:
        if os.path.isfile(os.path.join(pack, name)):
            shutil.copyfile(os.path.join(pack, name), os.path.join(out, name))
    fps = json.loads(read_text(os.path.join(pack, "fingerprints.json")) or "{}")
    kept, external, total = 0, [], 0
    for name in sorted(fps):
        p = os.path.join(pack, "sources", name)
        size = os.path.getsize(p) if os.path.isfile(p) else 0
        if os.path.isfile(p) and is_text(p) and total + size <= PROJECT_TEXT_MAX:
            shutil.copyfile(p, os.path.join(out, "sources", name))
            kept += 1
            total += size
        else:
            external.append(name)
    io.open(os.path.join(out, "external.txt"), "w", encoding="utf-8").write(u"\n".join(external) + u"\n")
    print("bundle: %d text sources for the Project; %d stored elsewhere (external.txt)" % (kept, len(external)))
    return 0


def external_names(pack):
    return set(l.strip() for l in read_text(os.path.join(pack, "external.txt")).splitlines() if l.strip())


def main(argv):
    if len(argv) >= 4 and argv[1] == "bundle":
        return bundle(argv[2], argv[3])
    if len(argv) < 3 or argv[1] not in ("collect", "recall", "verify"):
        print(__doc__)
        return 2
    cmd, pack = argv[1], argv[2]
    if cmd == "collect":
        ts, extra, i = [], [], 3
        while i < len(argv):
            if argv[i] == "--transcript" and i + 1 < len(argv):
                ts.append(argv[i + 1]); i += 2
            elif argv[i] == "--extra" and i + 1 < len(argv):
                extra.append(argv[i + 1]); i += 2
            else:
                i += 1
        collect(pack, ts or transcripts(pack), extra)
        return 0
    return recall(pack) if cmd == "recall" else verify(pack)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
