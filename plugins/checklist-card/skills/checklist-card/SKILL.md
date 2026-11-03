---
name: checklist-card
description: Convert someone's checklist from notes, a document, a photo or pasted text into a printable 5-step double-sided card (76 x 86 mm on A4) with cut lines. Use when asked to shorten a checklist, split a long one into cards, or prepare a card for a 5-row magnetic checklist holder.
---

# Checklist Card

Turn an existing checklist into cards of exactly the format below. The person's list is the source of truth: shorten and group its wording, but do not add steps of your own.

## Format

- Card 76 x 86 mm, both top corners clipped 16 x 4 mm, four cards per A4 sheet.
- Front: a title and exactly 5 rows. A step fits on up to 2 lines, about 60 characters.
- Back: a short title and "↑ Pull out". They show through two round openings in the holder, so the back title has at most 24 characters and no word over 12.
- Print on A4, double-sided, flip on long edge, 100% scale, with background graphics on.

This format comes from a prototype holder that has not been fit-tested in print. Say so if the person is about to print a large batch, and suggest one test sheet first. Check that the printed 100 mm line measures 100 mm.

## Workflow

1. **Read the source.** Copy the list faithfully, including sub-items. If a photo or scan is unclear, ask about the unclear words instead of guessing.
2. **Remove private data.** Leave out phone numbers, addresses, account details, passwords and other people's names unless the person explicitly wants them on a printed card.
3. **Choose the shape.**
   - Exactly 5 steps: use them.
   - Fewer than 5: leave the remaining rows empty, for writing by hand. Do not pad the list.
   - More than 5: group related items in one row ("Phone, charger, power bank"), or split the list into several themed cards. Propose the split when items would be lost.
4. **Keep what matters.** Never merge away or drop safety steps, medication, documents or anything the person marked as important. If they do not fit, make another card. List every item you dropped and ask before finalising.
5. **Write the rows.** Keep the language and the person's own words. Use one form across a card: all actions ("Close the windows") or all items ("Passport, cards"). Keep any required order.
6. **Write the job file**, using [examples/card.json](examples/card.json):
   `{"pull": "↑ Pull out", "cards": [{"title": "...", "back_title": "...", "steps": ["...", "...", "...", "...", "..."]}]}`
   `back_title` is optional. Add it when the title is too long for the back. `pull` sets the back label in the card's language.
7. **Build it:** `python scripts/make_card.py job.json cards.html --copies 1`. The script needs only Python and stops with a list of what does not fit. Fix the wording; do not cut text silently.
8. **Report.** Show the final rows, what you merged or dropped, and the printing settings. Open the HTML in a browser to print or save as PDF. The script checks lengths by character count, so look at the page before saying the text fits.
