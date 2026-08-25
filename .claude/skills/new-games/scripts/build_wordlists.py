#!/usr/bin/env python3
"""Regenerate data/words4.txt and data/words5.txt.

Requires the `wordfreq` package (`pip install wordfreq`) -- it ships its own
frequency data, no network access needed at run time. Takes the top N most
common English words, keeps the ones that are purely a-z (drops anything
with punctuation, numbers, or spaces), and splits by length.

Run this again if the word lists ever need refreshing:
    python3 build_wordlists.py
"""
import os
import re

from wordfreq import top_n_list

TOP_N = 50000  # ~3,900 4-letter and ~5,600 5-letter words at this cutoff
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def main():
    words = top_n_list("en", TOP_N)
    clean = sorted(set(w for w in words if re.fullmatch(r"[a-z]+", w)))

    for size in (4, 5):
        subset = [w for w in clean if len(w) == size]
        path = os.path.join(DATA_DIR, f"words{size}.txt")
        with open(path, "w") as f:
            f.write("\n".join(subset) + "\n")
        print(f"wrote {len(subset)} words to {path}")


if __name__ == "__main__":
    main()
