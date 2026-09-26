---
name: amsetup
description: >
  This skill should be used when the user types "/amsetup", or says "active-memory
  isn't working", "the hooks don't run", "python3 is not recognized", "it opens the
  Microsoft Store", "set up active-memory", or reports an error coming from the
  plugin. It checks what active-memory needs on this machine, explains what works
  without Python, and offers to install Python with the user's approval.
metadata:
  version: "0.2.0"
---

# active-memory setup check

Check this machine and report plainly. Never install anything without asking first.

## What needs what

| Part | Needs Python? |
|---|---|
| `/amcodeword`, `/amcheckpoint`, `/amhandoff`, `/amhelp` | No. These are instructions Claude follows, and they work everywhere, including the Claude apps. |
| Message counter and code word checker (Claude Code only) | Yes, any Python 2.7 or 3.x |

Say this clearly: without Python, the plugin still does its main job. Only the two automatic background checks are unavailable.

## Step 1: look for Python

Run these in the user's shell, stopping at the first that works:

- Windows: `py --version`, then `python --version`, then `python3 --version`
- macOS or Linux: `python3 --version`, then `python --version`

Report the result in one line, for example: "Python 3.12.1 found through `py`, so the automatic checks are working."

If a command opens the Microsoft Store or prints "not recognized", that name is a Windows placeholder, not a real Python. Keep checking the other names before concluding.

## Step 2: if no Python is installed

Tell the user what is affected (only the two automatic checks), then offer the install command for their system and **wait for a yes**:

| System | Command |
|---|---|
| Windows | `winget install -e --id Python.Python.3.12` |
| macOS | `brew install python` |
| Debian or Ubuntu | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |

Rules for this step:

- Ask before running anything. Never install silently, and never install without saying what it is.
- The install may ask for an administrator password or open a UAC prompt. Say so beforehand.
- If the user says no, that is fine. Confirm that the four commands still work, and stop.
- After installing on Windows, the user must open a new terminal before `py` is found. Say that.

## Step 3: confirm

Run the version check again and report whether the automatic checks are now active.

## If Python cannot be installed

The plugin still works. Tell the user:

- The four commands work as normal.
- Claude will still add checkpoints on its own when a chat gets long, just less reliably.
- They watch for the missing code word themselves, which is the intended way anyway.
- To silence any hook errors for good, delete `hooks/hooks.json` from the installed plugin folder.
