# Contributing to active-memory

Thanks for helping. Bug reports, ideas and fixes are all welcome.

## Report a bug

[Open a bug report](https://github.com/Klopyy/active-memory/issues/new?template=bug_report.yml). The form asks for:

- where it happened (Claude Code, the desktop app, claude.ai or Cowork)
- the command you ran and what you expected
- what happened instead
- your system, and the output of `py --version` or `python3 --version` if the bug is about the automatic checks

**Never paste passwords, keys or private chat content.** Cut the example down to the smallest thing that still shows the problem.

## Suggest an idea

[Open an idea](https://github.com/Klopyy/active-memory/issues/new?template=feature_request.yml). Say what problem it solves first, then the change you have in mind.

## Change the code

1. Fork the repo and create a branch.
2. Make your change. Keep the style of the files around it.
3. Run the checks:
   ```
   py tests/test_hooks.py
   claude plugin validate .
   ```
   On Mac or Linux use `python3` instead of `py`.
4. If you changed anything users see, update `README.md` and the version in `.claude-plugin/plugin.json` and in each `skills/*/SKILL.md`.
5. Open a pull request and describe what changed and how you tested it.

## House rules

- All commands start with `am`.
- The hooks must work with any Python (2.7 or any 3.x) and exit quietly when there is none. Never add a hard dependency.
- The plugin sends nothing over the network. Keep it that way.
- No long dashes in any file. Use a comma, a colon or a new sentence.
- Skill descriptions must not contain angle brackets, because the plugin installer rejects them.

## License

By contributing, you agree that your work is released under the [MIT License](LICENSE).
