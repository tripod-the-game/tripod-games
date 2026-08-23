#!/usr/bin/env python3
"""Regenerate data/vectors.npy and data/vocab.txt.

Requires spaCy with the en_core_web_lg model (NOT md -- md's vector table is
pruned to 20k entries with heavy hash-bucketing, which produces unreliable
similarity scores; lg ships ~343k unpruned vectors and calibrates far better
in practice, e.g. "weather"/"forecast" ranks high with lg but was buried
below unrelated pairs with md):
    pip install spacy
    python3 -m spacy download en_core_web_lg

Builds a compact word-vector table covering just the vocabulary this skill
actually needs, instead of shipping spaCy's full model:
  - every word that appears in an existing Tripod puzzle category name
    (pulled live from the tripod-games repo, so re-run this after a batch
    of new categories has been written, to keep coverage current)
  - the top N most common English words by frequency (via the `wordfreq`
    package, any length -- category names are arbitrary words like
    "Forecast" or "Wizardry", not just 4/5-letter puzzle answers, so this
    intentionally does NOT reuse new-games' length-restricted word lists)

Requires `wordfreq` too (`pip install wordfreq`) for the second part.

Run again if coverage gaps show up in practice:
    python3 build_vectors.py
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import spacy
from wordfreq import top_n_list

TOP_N_COMMON_WORDS = 30000

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
REPO_ROOT = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", ".."))
HELPER = os.path.join(REPO_ROOT, ".claude", "skills", "new-games", "scripts", "tripod_helper.py")


def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())


def collect_category_words():
    out = subprocess.run(
        [sys.executable, HELPER, "context", "--count", "1"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    names = list(data.get("one_off_categories_used_before", []))
    names += list(data.get("recurring_categories", {}).keys())
    words = set()
    for name in names:
        words.update(tokenize(name))
    return words


def collect_common_words():
    return set(w for w in top_n_list("en", TOP_N_COMMON_WORDS) if re.fullmatch(r"[a-z]+", w))


def main():
    vocab = collect_category_words() | collect_common_words()
    print(f"candidate vocab size: {len(vocab)}")

    nlp = spacy.load("en_core_web_lg")

    kept_words, vectors = [], []
    for word in sorted(vocab):
        tok = nlp.vocab[word]
        if tok.has_vector and tok.vector_norm > 0:
            kept_words.append(word)
            vectors.append(tok.vector)

    matrix = np.array(vectors, dtype=np.float32)
    print(f"words with real vectors: {len(kept_words)} (dim={matrix.shape[1]})")

    np.save(os.path.join(DATA_DIR, "vectors.npy"), matrix)
    with open(os.path.join(DATA_DIR, "vocab.txt"), "w") as f:
        f.write("\n".join(kept_words) + "\n")

    print(f"wrote {os.path.join(DATA_DIR, 'vectors.npy')} and vocab.txt")


if __name__ == "__main__":
    main()
