# Tripod Games — Generation Guide

## What is Tripod?

Tripod is a daily word puzzle where three words of equal length form a triangle, sharing letters at each corner. The player must find all three words given only a category hint.

## The Triangle Constraint (Critical)

Each puzzle uses either all **4-letter** or all **5-letter** words. The three words share letters at the three corners of the triangle:

```
         [apex]
        /      \
   wordOne    wordTwo
      \          /
       [wordThree]
```

- **Apex** — `wordOne[last]` = `wordTwo[first]`
- **Bottom-left** — `wordOne[first]` = `wordThree[first]`
- **Bottom-right** — `wordTwo[last]` = `wordThree[last]`

### Example: "Fruit" — GUAVA / APPLE / GRAPE

```
wordOne  = GUAVA  (G-U-A-V-A)
wordTwo  = APPLE  (A-P-P-L-E)
wordThree = GRAPE (G-R-A-P-E)
```

- Apex: GUAVA ends **A** = APPLE starts **A** ✓
- Bottom-left: GUAVA starts **G** = GRAPE starts **G** ✓
- Bottom-right: APPLE ends **E** = GRAPE ends **E** ✓

### Always verify all three constraints before finalising a puzzle

```
wordOne[last]  == wordTwo[first]   (apex)
wordOne[first] == wordThree[first] (bottom-left)
wordTwo[last]  == wordThree[last]  (bottom-right)
```

## File Format

```json
{
    "category": "Category Name",
    "size": 4,
    "wordOne": "word1",
    "wordTwo": "word2",
    "wordThree": "word3"
}
```

- `size` is optional — omit it and it defaults to **5**. Only include it when using **4-letter** words.
- Words should be **lowercase**.
- Files are named `MMDDYY.json` and listed in `index.json`.

---

## What Makes a Great Game

### 1. Strong thematic coherence
All three words must clearly and independently belong to the category. The player should have an "aha" moment when the category clicks. If any word feels like a stretch, rethink it.

### 2. Interesting categories
The best categories are specific enough to be surprising but broad enough that the words feel inevitable in hindsight. Great categories from the existing library include:

- **Simple themes**: "Fruit", "Hardware", "Golf", "Fishing"
- **Emotional/abstract**: "Courage", "Yearn", "State of Panic"
- **Pop culture**: "Taylor Swift Songs", "Breaking Bad", "Buffy the Vampire Slayer"
- **Niche/specific**: "Wading Birds", "Figure Skating Movements", "Ordinal Numbers"
- **Fill-in-the-blank**: "En-____", "Re-_____", "De-____", "____-ful", "____-out"
- **Wordplay**: "Anagrams with 'V'", "Edible O's", "Comic Book Noises"
- **Activity + context**: "Orders at the Bar", "Debug (Code)", "On the Farm"
- **Proper nouns**: "Countries", "European Cities", "Disney Leading Ladies"

### 3. Word quality
- Use common, recognisable words — avoid obscure vocabulary unless the category specifically calls for it
- Proper nouns are fine when the category expects them (names, places, brands, characters)
- Avoid plurals where possible — singular forms make for cleaner puzzles
- All three words should feel equally "at home" in the category, not one strong and two fillers

### 4. The hidden constraint
The triangle constraint is what makes it a puzzle. Players don't see the corner rules — they only see the category and the empty grid. The best puzzles have words that feel naturally connected to the category first, with the geometric constraint as a satisfying hidden structure.

---

## Generation Process

### Step 1 — Pick a category
Think of a theme with many possible words. The constraint will narrow the field significantly, so start with themes that have 10+ candidate words.

### Step 2 — Pick corner letters
Choose three letters: **BL** (bottom-left, shared by wordOne and wordThree starts), **Apex** (shared by wordOne end and wordTwo start), **BR** (bottom-right, shared by wordTwo end and wordThree end).

This gives you the pattern:
- wordOne: `BL _ _ Apex` (4-letter) or `BL _ _ _ Apex` (5-letter)
- wordTwo: `Apex _ _ BR` (4-letter) or `Apex _ _ _ BR` (5-letter)
- wordThree: `BL _ _ BR` (4-letter) or `BL _ _ _ BR` (5-letter)

### Step 3 — Find words that fit
With the pattern established, look for category words that match. Often easier to find wordOne and wordThree first (they share a starting letter), then find wordTwo.

### Step 4 — Verify
Check all three constraints explicitly before writing the JSON.

---

## Common Pitfalls

- **Forgetting which constraint is which** — the apex connects wordOne's *end* to wordTwo's *start*; the bottom corners connect *starts* of wordOne/wordThree and *ends* of wordTwo/wordThree
- **One word doesn't fit the category** — all three must belong equally; don't use a word just because it satisfies the constraint
- **Category too vague** — "Things" or "Words" aren't categories; be specific
- **Category too obscure** — if the average player wouldn't know 2 of the 3 words, the puzzle isn't fun
- **Repeated words across consecutive days** — check recent games before publishing

---

## Quick Reference: Verified Examples

### 4-Letter

| Category | wordOne | wordTwo | wordThree |
|----------|---------|---------|-----------|
| Golf | chip | putt | cart |
| Fishing | bait | tide | bite |
| Poker | card | deal | call |
| Sea Sailing | ship | port | salt |
| ____-out | call | look | cook |

### 5-Letter

| Category | wordOne | wordTwo | wordThree |
|----------|---------|---------|-----------|
| Fruit | guava | apple | grape |
| In the Ocean | shark | krill | shell |
| Geology | shale | erode | stone |
| Liquid Toppings | syrup | puree | sauce |
| On the Farm | steer | range | swine |
