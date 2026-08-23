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

3. **Design each puzzle using the bundled dictionary, not guesswork.** `data/words4.txt` and
   `data/words5.txt` are real, frequency-filtered English word lists (~2,600 and ~3,600 words) bundled
   with this skill — don't rely on words you can personally recall fitting a pattern, since that misses
   real matches and occasionally invents non-words. Two ways to use them, matching CLAUDE.md's Step 2-3:

   - **Words first:** brainstorm 8-15 words you believe belong to the category, then run
     ```
     python3 .claude/skills/new-games/scripts/tripod_helper.py search <size> '["word1","word2",...]'
     ```
     It tells you which of your words aren't in the dictionary (drop or double-check those — could be a
     proper noun, which is fine, or a typo/rare word, which isn't) and returns *every* valid triangle
     among the rest, each pre-flagged with any recent-reuse warning. This is exact — it will surface
     combinations you wouldn't have spotted by hand.
   - **Letters first:** if you've picked BL/apex/BR corner letters, run
     ```
     python3 .claude/skills/new-games/scripts/tripod_helper.py pattern <size> <pattern>
     ```
     with `_` as a wildcard (e.g. `pattern 5 c___t` for 5-letter words starting `c`, ending `t`) to see
     every real word that could fill that slot, then judge which ones fit your category.

   Either way, prefer words not in `word_last_used` at all; if you do reuse one, check its `days_ago` and
   keep it comfortably above `word_reuse_min_days_norm` (20) — otherwise pick a different word. The
   dictionary confirms a word is *real and reasonably common*; it doesn't know what's thematically
   strong or too obscure for the category — that judgment call is still yours, per CLAUDE.md's guidance.

4. **Verify every candidate before presenting it.** Run:
   ```
   python3 .claude/skills/new-games/scripts/tripod_helper.py verify '<json>'
   ```
   with the candidate as a compact JSON object, e.g.
   `{"category":"Fruit","size":5,"wordOne":"guava","wordTwo":"apple","wordThree":"grape"}`.
   This checks the triangle constraint precisely (don't trust hand-verification for this — the script is
   exact) plus word length/format and re-checks recent category/word usage. Fix and re-run until `"ok":
   true` with no warnings you can't justify. Do this for all 3 candidates before showing them to the user.

5. **Check each category name against the corpus semantically**, not just for exact repeats. `verify`
   only catches an identical category string; it won't catch a fresh-sounding name that's really the
   same idea in different words (e.g. "Forecast" reads as new next to an existing "Weather" category
   until you check). Run:
   ```
   python3 .claude/skills/category-similarity/scripts/check_similarity.py "<category name>"
   ```
   for each candidate category. It ranks existing categories by semantic closeness — read the top match
   and use judgment (it's a screening aid, not a hard gate; see that skill's own docs for what its scores
   do and don't mean). If the top match is a near-synonym, swap in a different angle on the category
   before presenting it.

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
