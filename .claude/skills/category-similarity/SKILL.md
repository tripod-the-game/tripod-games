---
name: category-similarity
description: Check whether a candidate Tripod puzzle category name is semantically too close to a category already used in this repo's history (e.g. "Forecast" vs. the existing "Weather", or "Backpacking" vs. the existing "Camping") — catches thematic overlap that a plain string/duplicate check would miss. Use this whenever proposing or finalizing a new category name for a Tripod daily puzzle, especially as a companion step inside the new-games skill's workflow, or whenever the user asks something like "is this category too similar to an existing one" or "would X and Y categories feel redundant next to each other."
---

# Category Similarity Check

Existing categories in this repo are tracked by exact name (`new-games`' `context` command already
flags exact repeats). What that can't catch is a *new* name that's really the same idea in different
words — "Forecast" reads as fresh next to "Weather" until a player notices both puzzles lean on the same
handful of words. This skill runs a semantic-similarity check to surface that before it ships.

## How it works

```
python3 .claude/skills/category-similarity/scripts/check_similarity.py "<candidate category>" --top 5
```

This embeds the candidate name and every category already in the repo's history (pulled live via
`new-games`' `context` command) using precomputed word vectors, then prints the existing categories
ranked by cosine similarity to the candidate.

**Read this as a screening aid, not a verdict.** In calibration testing:
- "Forecast" correctly surfaced "Weather" (0.68) and "Winter Storm" (0.50) at the top.
- "Backpacking" correctly surfaced "Camping" (0.74) and "Mountaineering" (0.69) at the top.
- But scores don't cleanly separate "too close to coexist" from "related but fine as distinct
  categories" — e.g. "Skiing" vs. an already-used "Snowboarding"-style category would also score high,
  even though two winter-sport categories can reasonably both exist in the corpus. A high score means
  "look at this pair and use judgment," not "reject automatically."

If the candidate's words aren't common enough to be in the bundled vocabulary, the script says so
(`"error": "no vocabulary overlap"` or `unrecognized_words_in_candidate`) instead of guessing — a miss
there just means fall back to manual judgment for that name, the same as before this skill existed.

## When to use it

- While finalizing categories in the `new-games` workflow, run this on each candidate category name
  after picking it (and before presenting it) alongside `tripod_helper.py verify`. It's a cheap extra
  check, not a replacement for verify's exact-duplicate and word-recency checks.
- Standalone, whenever asked to sanity-check one category name, or to compare two proposed names against
  each other directly (run the tool once per name and compare which existing categories each surfaces).

## Maintenance

The word vectors (`data/vectors.npy`, `data/vocab.txt`) are precomputed and bundled so this check runs
with only `numpy` at request time — no spaCy, no model download, no network call. Regenerate them with
`scripts/build_vectors.py` (needs `pip install spacy && python3 -m spacy download en_core_web_lg`, plus
`wordfreq`) after a large batch of new categories has been written to the repo, so the comparison set
stays current. Read that script's docstring before changing which spaCy model it uses — the default
`md` model's pruned vector table gave unreliable scores in testing (see the docstring for specifics);
`lg` is required for the calibration numbers above to hold.
