---
name: new-games
description: Generate candidate new daily Tripod puzzles (category + three triangle-linked words) for this repo, following the rules in CLAUDE.md. Use this whenever the user asks to create, brainstorm, propose, draft, or come up with new daily game(s)/puzzle(s) for Tripod, or asks "what should tomorrow's game(s) be" — even if they don't name this skill directly. This only proposes candidates for review; it does not write puzzle files to the repo.
---

# New Tripod Games

Propose new daily Tripod puzzles: a category plus three words (`wordOne`, `wordTwo`, `wordThree`) that
share letters at the corners of a triangle, per the rules in this repo's `CLAUDE.md`. Read that file
first if it's not already in context — it defines the triangle constraint, the JSON format, and what
makes a category/word choice good.

This skill only *proposes* candidates for the user to review. Never write a puzzle file into
`20XX/MM/MMDDYY.json` or edit `index.json` unless the user explicitly asks you to commit one of the
candidates after seeing it.

## Why the history check matters

A puzzle that's geometrically valid but reuses last week's category, or a word from ten days ago, is a
worse puzzle even though it "passes." The repo's own history (229 games so far) shows the house style:
categories almost never repeat (only a handful of intentionally recurring buckets like "No Category
Sunday" do, and only on their fixed weekday), and reused words are normally spaced 20+ days apart. A
freshly generated candidate should follow that pattern, not just satisfy the corner-letter math.

## Workflow

1. **Load history.** Run:
   ```
   python3 .claude/skills/new-games/scripts/tripod_helper.py context --count 3
   ```
   This returns JSON with: the latest date already on record, the next 3 unused calendar dates (with
   weekday — flag any that land on Sunday, since this repo's convention is a themeless "No Category
   Sunday" puzzle on Sundays), every category ever used with how many times and how recently, and every
   word ever used with how many days ago. Use `--count` to get more dates if asked for more than 3 games.

2. **Pick three categories**, one per target date. For each:
   - Prefer a category not in `one_off_categories_used_before` at all.
   - If the target date is a Sunday, "No Category Sunday" (freeform, no theme) is the established
     pattern — offer it as the natural choice for that slot, but a real theme is fine too if it's strong.
   - Otherwise avoid every category in `one_off_categories_used_before` and `recurring_categories`
     unless you have a specific reason to intentionally revive one (say so if you do).
   - Follow CLAUDE.md's guidance on what makes a category good: specific but not obscure, 10+ candidate
     words in your head before you commit to it.

3. **Design each puzzle** per CLAUDE.md's Step 2-3 (pick BL/apex/BR corner letters, then find category
   words that fit the pattern). Prefer words not in `word_last_used` at all; if you do reuse one, check
   its `days_ago` and keep it comfortably above the `word_reuse_min_days_norm` (20) — otherwise pick a
   different word.

4. **Verify every candidate before presenting it.** Run:
   ```
   python3 .claude/skills/new-games/scripts/tripod_helper.py verify '<json>'
   ```
   with the candidate as a compact JSON object, e.g.
   `{"category":"Fruit","size":5,"wordOne":"guava","wordTwo":"apple","wordThree":"grape"}`.
   This checks the triangle constraint precisely (don't trust hand-verification for this — the script is
   exact) plus word length/format and re-checks recent category/word usage. Fix and re-run until `"ok":
   true` with no warnings you can't justify. Do this for all 3 candidates before showing them to the user.

## Output format

Present exactly 3 candidates (unless the user asked for a different number), each like this:

```
### [Target date, e.g. 081926 (Wednesday)]
Category: <category>
Size: <4 or 5>
  wordOne   = <word>
  wordTwo   = <word>
  wordThree = <word>

Verified:
  apex        wordOne[last]='<x>'  == wordTwo[first]='<x>'   ✓
  bottom-left wordOne[first]='<x>' == wordThree[first]='<x>' ✓
  bottom-right wordTwo[last]='<x>' == wordThree[last]='<x>'  ✓
```

After the three candidates, briefly note anything worth flagging (e.g. "Friday's puzzle reuses the word
X from Y days ago, which is a bit tighter than usual" or "Sunday's slot uses the No Category convention").
Then ask if the user wants any of them written to the repo — don't write files unprompted.
