# active-memory handoff: Yacht Lift Tariff Calculator

**Handoff #1** · 2026-09-17 · Lineage: #1 (2026-09-17): Initial planning session: pricing rules, layout, styling, and business rules defined; no code written yet.

## 0. Instructions for Claude (read first)

You are continuing work from a previous chat. That chat is gone; this file is the complete context and the source of truth.

1. Read this whole file before replying.
2. Follow sections 3 (Style), 4 (Hard rules) and 5 (Corrections) in every reply, for the rest of this chat. They override your defaults.
3. Use the values in section 8 exactly. Never round, re-estimate, or "correct" them.
4. Do not suggest anything listed in section 7 (Changed / rejected) again unless the user brings it up.
5. Code word: Start every reply with exactly "Yes Boss!"
6. Your first reply: at most 5 lines covering the goal, the current state, and the next step (section 11). Mention any files from section 13 that were not attached. Ask the questions in section 12 if there are any. End with "Ready to continue with <next step>?" Then wait for the user's go.

## 1. Mission
- **Goal:** Build a yacht lift tariff calculator web page for a shipyard in Sharm El Sheikh.
- **Done looks like:** A working `yacht-lift-tariff.html` page where Mona (accounting) enters boat details and gets an accurate price breakdown per the shipyard's rules, in Arabic RTL, with correct VAT, surcharges, and edge-case handling (oversize boats).
- **Why it matters / context:** Used daily by accounting staff to quote lift/storage prices; prices are ultimately approved by Captain Hany.

## 2. About the user (as relevant to this work)
- Runs/represents a shipyard business in Sharm El Sheikh, Egypt.
- Key staff: Captain Hany (approves all prices, must manually approve boats over 24m), Mona (accounting, will use the calculator daily).
- Currently in planning-only mode, explicitly asked not to write code until told to.

## 3. Style & communication
- **Language:** English replies from Claude; all page UI text must be Arabic, RTL.
- **Tone:** Direct, no fluff.
- **Reply length:** Short.
- **Formatting:** No emojis in replies.
- **Working style:** Plan first, confirm each business rule individually before building; user gives rules incrementally across many messages.
- **Avoid:** Emojis, long replies, starting to code before explicit go-ahead.

## 4. Hard rules (word for word)
1. "all UI text must be Arabic RTL, but numbers always stay in Western digits (0-9)"
2. "don't write any code until I say" (planning phase only)
3. "never use red for any button. Use navy #1B2A4A for primary buttons."
4. "Keep your replies short and no emojis please."
5. Filename must be `yacht-lift-tariff.html`.
6. Arabic font: Cairo.

## 5. Corrections log
| # | Claude did | The user wanted |
|---|---|---|
| 1 | Proposed a results table with "المبلغ" (amount) column ambiguous in RTL rendering | Explicit confirmation: Amount/Total column must sit on the LEFT side of the RTL page (item column on the right), since totals read last in RTL |
| 2 | Assumed storage days counted as a simple date difference | Storage days are inclusive of both the lift-in day and the lift-out day |
| 3 | File was initially named `tariff.html` | Renamed to `yacht-lift-tariff.html`: "tariff.html is too generic" |
| 4 | Weekend surcharge locked in at 10% | User later said they're unsure, might be 15%, needs to confirm with Captain Hany (currently unconfirmed, kept at 10% as placeholder) |

## 6. Decisions
| Decision | Why |
|---|---|
| No PDF export button | Too heavy to implement now; browser print-to-PDF covers the need |
| No quote-saving/history in v1 | Not needed yet; user said "maybe later" |
| Boats >24m get a warning instead of a price | Requires Captain Hany's manual approval |
| Primary button color navy #1B2A4A, never red | User's explicit brand/UX rule |
| Arabic font: Cairo | User's explicit choice |
| Results table: item column right, amount/total column left | Matches RTL reading order (totals read last) |

## 7. Changed / rejected
- PDF export button → rejected, replaced with browser print-to-PDF (CSS print styles)
- Filename `tariff.html` → renamed to `yacht-lift-tariff.html`
- Weekend surcharge 10% → flagged uncertain, possibly 15%, pending confirmation with Captain Hany (not yet resolved, see Open questions)

## 8. Data & facts (exact)
| Item | Value |
|---|---|
| Lifting fee | 1,250 EGP per meter of boat length |
| Lifting minimum | 8 meters (boats under 8m billed as if 8m) |
| Storage fee | 95 EGP per meter per day |
| Storage day counting | Inclusive of both lift-in day and lift-out day |
| VAT | 14%, applied to everything (lifting + storage + add-ons) |
| Weekend surcharge | Friday & Saturday lifting: +10%, **UNCONFIRMED, may be 15%, pending Captain Hany** |
| Pressure washing | Flat 600 EGP per boat, optional add-on |
| Oversize threshold | Boats over 24m: no automatic price, show warning requiring Captain Hany's manual approval |
| Primary button color | Navy #1B2A4A (no red anywhere) |
| Arabic font | Cairo (Google Fonts) |
| File name | `yacht-lift-tariff.html` |
| Admin password (settings panel) | [secret removed: re-enter it] |
| Mooring (in-water stay) section | Planned for later; prices not yet provided by user; backlog item, not blocking current build |

## 9. People, terms & names
- **People:** Captain Hany: approves all prices, must manually approve any quote for boats over 24m. Mona: accounting staff, will use the calculator daily.
- **Terms:** "Lifting" = crane lift fee; "Storage" = on-land storage fee; "Mooring" = future section for boats staying in water instead of on land.
- **Names in use:** File `yacht-lift-tariff.html`.

## 10. Work state
| Item | Status | Version / location | Notes |
|---|---|---|---|
| yacht-lift-tariff.html | Not started | N/A | All pricing rules, layout direction, and styling rules agreed; no code written per user's explicit instruction |
| Results table layout | Design agreed (not coded) | N/A | Item column right, amount/total column left, RTL |
| Pricing formula | Defined (not coded) | N/A | See section 8 |

## 11. Next steps
1. **Next action:** Confirm the weekend surcharge percentage (10% vs 15%) with Captain Hany.
2. Resolve remaining open pricing questions (section 12).
3. Once confirmed, begin coding `yacht-lift-tariff.html` (only after explicit user go-ahead).

## 12. Open questions ⚠️
- Weekend surcharge: is it 10% (as originally stated) or 15% (user's later uncertainty)? Needs Captain Hany's confirmation.
- Does the 8-meter minimum apply to storage calculations too, or only to lifting?
- Can boat length be entered with decimals (e.g. 12.5m)? If so, how do partial meters round for billing?
- Is storage optional (some boats lift and leave same day), or always charged?
- Does the weekend surcharge apply only to lifting, or also to storage?
- Mooring (in-water) section prices: not yet provided by user.

## 13. Re-attach checklist
Nothing to attach: no files were created during this session (planning only).

---
<sub>Audit: 13/13 sections · 6 rules · 4 corrections · 12 data points · secrets removed: yes · generated by active-memory</sub>
