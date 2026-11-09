---
name: document-review
description: Integrity review for any document about to leave your company — SOW, proposal, contract, minutes, report, deck. Checks internal consistency, formatting, numbers, and loose ends a client could question. Run it after generating or editing any document, before handing it over.
---

# Document Review — Integrity Gate

deslop judges the *prose*. This judges the *document*: does it contradict itself, does the formatting hold, do the numbers add up, and what will the client ask that it fails to answer.

Run on every document before handover. Report findings by severity. Fix formatting-only defects yourself; **never silently change commercial or legal terms** - flag those for the document owner.

## 1. Identity and dates

- Client **legal** name correct and identical everywhere (not the trading name in one place and the entity in another).
- The right entity is named. Where a group has multiple entities and prior documents disagree, flag it rather than picking.
- Document date matches any date in the footer or header.
- Preparer name, title, address, phone, email correct, accents included.
- Signatory names and titles are the real ones for this account, and the right people for *this* client (not a default set copied from another).
- Your own company's signatory is never a finding when anyone in the company can sign, so do not ask whether the named person is authorized, and do not ask for a secretary's certificate or board resolution.

## 2. Header and footer regions — check these visually, always

The single highest-risk area, because these regions are nearly invisible while editing:

- **Google Docs find-and-replace reaches headers and footers but reports "0 of 0"** because the match counter only tallies body matches. A search that looks like it found nothing proves nothing. Open page 2 and read the header with your eyes.
- Stale text from the source document is the classic failure. A real SOW went out carrying another project's name in its running header, inherited from the doc it was built from.
- Header text must fit on **one line**. Replacement text of the same character count can still wrap, because caps and letter widths differ. Look, don't count.
- Page numbers present and starting where intended.

## 3. Heading structure

Open the document outline (Docs: the ☰ panel). Every section header must appear in it.

- Headers that are manually styled (font size + bold) instead of a real Heading style **look correct but are invisible to the outline and to any table of contents**. In one real SOW, 8 of 12 section headers were manual, so only OVERVIEW, OBJECTIVE and ACCEPTANCE appeared in the outline.
- Body paragraphs wrongly given a Heading style pollute the outline. Look for a heading entry that reads like a sentence.
- **Do not bulk-restyle a document that is about to be signed.** Two traps, both hit live: applying "Normal text" can switch the font, because the Normal style may be defined as a different face than the body uses (Open Sans vs Google Sans), and re-applying a paragraph style can strip bold runs inside the paragraph. If you do restyle, verify font *and* inline bold afterward, and undo if either moved. When the document has no TOC, the outline issue is cosmetic - flag it and leave it.

## 4. Self-consistency

- **The document calls itself one thing throughout.** A doc titled "Statement of Work" must not say "This Supplement covers..." in the body. Check every self-reference.
- Defined terms ("Provider", "Client") are defined once and then used, not mixed with raw names.
- **Every referenced document is named and dated.** "under the support terms of the Agreement" is a loose end if no Agreement is identified anywhere in the doc - a client's lawyer will ask which agreement.
- Terminology matches the client's own vocabulary and stays fixed (don't alternate pod/team, funder/contact, admin/user).

## 5. Section promises vs contents

Read each header, then check the body delivers what it advertises. A section titled "FIXED COST **& PAYMENT SCHEDULE**" containing only a price table and no payment trigger, schedule, or due date is an unanswered question sitting under a promise. This exact gap survived into a signing-ready SOW.

## 6. Numbers

- Line items sum to the stated total.
- Effort × rate = line amount, for every row.
- Currency stated explicitly; tax treatment stated (VAT-exclusive / inclusive, withholding, bank fees).
- Percentages in a payment schedule total 100%, and the amounts match the percentages.
- Any cap, quantity, or volume figure traces to something the client actually said - a guessed cap must be flagged, not quietly shipped.
- Every figure the reader is told to hold on to (a headline number, a saving, a count) appears later with the same value. A script that leads with 9M and closes on 3k fails (ML demo, retro 10-16).

## 7. Loose ends a client will ask about

Go through as the counterparty and list what you would ask. Recurring gaps:

- **When?** No timeline or delivery window anywhere.
- **How and when do I pay?** Trigger, invoice timing, payment terms.
- **What happens after delivery?** Warranty or explicitly no warranty, and where support lives.
- **What is not included?** If OUT OF SCOPE was dropped, confirm the Change Request section really carries that weight.
- **What are you assuming of me?** Client responsibilities and dependencies stated.
- Anything the doc leaves to inference about money, time, or scope.
- **The owner's open questions.** "To confirm", "TBD", "open question", a Decisions-to-make section: the doc fails. Settle each one first, deciding it yourself where the company can, and asking the owner with the picker where it is their call. Docs should decide.

## 8. Pagination and layout

Scroll every page:

- No heading orphaned at the bottom of a page with its body overleaf.
- No table split across a page break.
- Signature block not split across pages.
- Cover page contains only cover material - body sections must not spill onto it.
- No stranded blank page at the end.
- Fix by adding or removing a page break, not by rewording.
- No table header row on one page with its body on the next. In Google Docs, pin the header row and set every row to not break across pages; a short table that still splits gets a page break before its heading (Docs ignores keep-with-next inside cells).
- In our own template, every table header row carries the same fill and text color, and each heading level has one color. Check all of them, not the one that was flagged.
- No uneven gaps between sections: blank paragraphs before headings, stray page breaks, or keep-lines-together on body text all leave holes.
- No MVP 2 or later rows inside a table headed for MVP 1.

## 9. Leftovers

- No `{{PLACEHOLDER}}`, `[TBD]`, `XXX`, lorem text, or template example content.
- No tracked leftovers from the source document: another client's name, a stale project name, an old date, a previous rate.
- Links resolve and point where the text claims.
- No stray comments or suggestions left open.

## Output

Report as: **Blocking** (wrong facts, contradictions, missing commercial terms), **Should fix** (formatting, consistency, loose ends), **Note** (cosmetic). For each: what it is, where, and the concrete fix. Then state plainly which ones you fixed and which need his call.

If a fix regresses anything, say so and revert - a signing-ready document is not the place to leave an experiment.

## When findings get posted as comments

Findings that go into someone else's document from his account are written to a colleague, so they must not read as blunt (he rewrote most of the DOE HTC comments on 2026-10-06 for sounding rude).

- Give the reason first, in plain words, with "we" and "our".
- Offer the change as a question or a "maybe": "should we cite the exact section?", "maybe we check with them before we send".
- A risk is a question to the author: "Would BAC or legal flag this?" Not "will", and not "might" either.
- No "fix:" label, no orders, nothing that points at what the author missed.
- Commercial terms the author chose are deliberate: billing schedule, prepayment, payment triggers, pricing structure. Do not post a suggestion that changes them (he deleted the billing-timeline suggestions on the DOE doc; Chelle set up prepayment on purpose). If one looks risky, raise it to him privately as one question.

