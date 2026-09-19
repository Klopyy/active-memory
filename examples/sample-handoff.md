# active-memory handoff: Sunny Paws Booking Page

**Handoff #1** · 2026-09-17 · Lineage: #1 (2026-09-17): Planning session: pricing, layout, styling and booking rules agreed; no code written yet.

## 0. Instructions for Claude (read first)

You are continuing work from a previous chat. That chat is gone; this file is the complete context and the source of truth.

1. Read this whole file before replying.
2. Follow sections 3 (Style), 4 (Hard rules) and 5 (Corrections) in every reply, for the rest of this chat. They override your defaults.
3. Use the values in section 8 exactly. Never round, re-estimate, or "correct" them.
4. Do not suggest anything listed in section 7 (Changed / rejected) again unless the user brings it up.
5. Code word: Start every reply with exactly "Yes Boss!"
6. Your first reply: at most 5 lines covering the goal, the current state, and the next step (section 11). Mention any files from section 13 that were not attached. Ask the questions in section 12 if there are any. End with "Ready to continue with <next step>?" Then wait for the user's go.

## 1. Mission
- **Goal:** Build a booking page for Sunny Paws, a small dog-walking business.
- **Done looks like:** A working `sunny-paws-booking.html` where a customer picks a walk, adds dogs and a date, and sees an exact price before booking.
- **Why it matters / context:** Replaces booking by text message; Leo handles bookings every day and Priya sets all prices.

## 2. About the user (as relevant to this work)
- Builds the site for Sunny Paws; comfortable with HTML, prefers to review a plan before any code.
- Key people: Priya (owner, sets and approves all prices), Leo (takes the bookings, will use the page daily).
- Currently in planning-only mode, explicitly asked not to write code until told to.

## 3. Style & communication
- **Language:** English.
- **Tone:** Direct, no fluff.
- **Reply length:** Short.
- **Formatting:** No emojis in replies.
- **Working style:** Plan first, confirm each business rule one at a time; rules arrive across many messages.
- **Avoid:** Emojis, long replies, starting to code before an explicit go-ahead.

## 4. Hard rules (word for word)
1. "prices always in USD with two decimals, like $18.00"
2. "don't write any code until I say" (planning phase only)
3. "never use red anywhere. Primary buttons are teal #0F766E."
4. "Keep your replies short and no emojis please."
5. File name must be `sunny-paws-booking.html`.
6. Font: Inter.

## 5. Corrections log
| # | Claude did | The user wanted |
|---|---|---|
| 1 | Put the price column on the left of the summary table | Price column on the RIGHT, right-aligned, so totals line up |
| 2 | Counted walk time from the booking time | Walk time counts from pickup to drop-off |
| 3 | Named the file `form.html` | Renamed to `sunny-paws-booking.html`: "form.html is too generic" |
| 4 | Locked the holiday surcharge at 20% | User later said they're unsure, might be 25%, needs Priya's confirmation (kept at 20% as a placeholder) |

## 6. Decisions
| Decision | Why |
|---|---|
| No "Download PDF receipt" button | Too heavy for now; the browser's print-to-PDF covers it |
| No customer accounts in v1 | Not needed yet; user said "maybe later" |
| Dogs over 40 kg get a message instead of a price | Priya approves large dogs by hand |
| Primary buttons teal #0F766E, never red | User's explicit rule |
| Font: Inter | User's explicit choice |
| Summary table: item on the left, price on the right | Totals line up and read last |

## 7. Changed / rejected
- "Download PDF receipt" button → rejected, replaced with browser print-to-PDF (print styles)
- File name `form.html` → renamed to `sunny-paws-booking.html`
- Holiday surcharge 20% → flagged uncertain, possibly 25%, pending Priya (see Open questions)

## 8. Data & facts (exact)
| Item | Value |
|---|---|
| 30-minute walk | $18.00 per dog |
| 60-minute walk | $30.00 per dog |
| Minimum billing | Walks under 30 minutes are billed as 30 minutes |
| Extra dog, same household | +$8.00 per extra dog |
| Holiday surcharge | +20% on public holidays, **UNCONFIRMED, may be 25%, pending Priya** |
| Sales tax | 8.25%, applied to the full total |
| Large dog threshold | Over 40 kg: no automatic price, show a message asking for Priya's approval |
| Primary button color | Teal #0F766E (no red anywhere) |
| Font | Inter (Google Fonts) |
| File name | `sunny-paws-booking.html` |
| Admin password (settings panel) | [secret removed: re-enter it] |
| Cat-sitting section | Planned for later; prices not given yet; backlog, not blocking |

## 9. People, terms & names
- **People:** Priya: owner, sets and approves all prices, approves dogs over 40 kg. Leo: takes the bookings, will use the page daily.
- **Terms:** "Walk" = one booked walk for one or more dogs from the same household; "Holiday" = a public holiday on the booking date.
- **Names in use:** File `sunny-paws-booking.html`.

## 10. Work state
| Item | Status | Version / location | Notes |
|---|---|---|---|
| sunny-paws-booking.html | Not started | N/A | All pricing, layout and styling rules agreed; no code written per the user's explicit instruction |
| Summary table layout | Design agreed (not coded) | N/A | Item left, price right, right-aligned |
| Pricing formula | Defined (not coded) | N/A | See section 8 |

## 11. Next steps
1. **Next action:** Confirm the holiday surcharge (20% or 25%) with Priya.
2. Resolve the remaining open questions (section 12).
3. Once confirmed, start coding `sunny-paws-booking.html` (only after an explicit go-ahead).

## 12. Open questions ⚠️
- Holiday surcharge: 20% (said first) or 25% (later uncertainty)? Needs Priya's confirmation.
- Does the 30-minute minimum also apply to 60-minute walks that end early?
- Can customers book several dates at once?
- Is sales tax shown as its own line or included in each price?
- Does the holiday surcharge apply to the extra-dog fee too?
- Cat-sitting prices: not given yet.

## 13. Re-attach checklist
Nothing to attach: no files were created during this session (planning only).

---
<sub>Audit: 13/13 sections · 6 rules · 4 corrections · 12 data points · secrets removed: yes · generated by active-memory</sub>
