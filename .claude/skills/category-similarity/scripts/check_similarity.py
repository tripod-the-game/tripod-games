#!/usr/bin/env python3
"""Rank existing Tripod categories by semantic closeness to a candidate name.

Usage:
    python3 check_similarity.py "Forecast"
    python3 check_similarity.py "Forecast" --top 8

Runtime-only dependency: numpy. The word vectors were precomputed offline by
build_vectors.py (which needs spaCy) so this script stays lightweight.

This is a screening aid, not a verdict. Cosine similarity on averaged word
vectors is a coarse signal -- in testing, genuinely-too-close pairs and
perfectly-fine-to-coexist pairs did not fall into clean score bands (e.g.
"skiing"/"snowboarding", which are fine as separate categories, scored
higher than "weather"/"forecast", which probably shouldn't both exist).
Always read the actual top matches and use judgment; don't gate on a
threshold alone.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
REPO_ROOT = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", ".."))
HELPER = os.path.join(REPO_ROOT, ".claude", "skills", "new-games", "scripts", "tripod_helper.py")


def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())


def load_vectors():
    vocab_path = os.path.join(DATA_DIR, "vocab.txt")
    vectors_path = os.path.join(DATA_DIR, "vectors.npy")
    with open(vocab_path) as f:
        words = [w.strip() for w in f if w.strip()]
    matrix = np.load(vectors_path)
    return dict(zip(words, matrix))


def embed(text, vectors):
    tokens = tokenize(text)
    found = [vectors[t] for t in tokens if t in vectors]
    missing = [t for t in tokens if t not in vectors]
    if not found:
        return None, missing
    vec = np.mean(found, axis=0)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return None, missing
    return vec / norm, missing


def fetch_existing_categories():
    out = subprocess.run(
        [sys.executable, HELPER, "context", "--count", "1"],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    names = list(data.get("one_off_categories_used_before", []))
    names += list(data.get("recurring_categories", {}).keys())
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("category", help="candidate category name to check")
    parser.add_argument("--top", type=int, default=5, help="how many closest matches to show")
    args = parser.parse_args()

    vectors = load_vectors()
    candidate_vec, missing = embed(args.category, vectors)

    if candidate_vec is None:
        print(json.dumps({
            "candidate": args.category,
            "error": "no vocabulary overlap -- all words unrecognized, cannot compare",
            "unrecognized_words": missing,
        }, indent=2))
        sys.exit(1)

    existing = fetch_existing_categories()
    scored = []
    all_missing = set(missing)
    for name in existing:
        vec, miss = embed(name, vectors)
        all_missing.update(miss)
        if vec is None:
            continue
        score = float(np.dot(candidate_vec, vec))
        scored.append({"category": name, "score": round(score, 3)})

    scored.sort(key=lambda x: -x["score"])

    print(json.dumps({
        "candidate": args.category,
        "unrecognized_words_in_candidate": missing or None,
        "closest_existing_categories": scored[:args.top],
        "note": (
            "Scores are a coarse similarity signal (see this script's docstring), "
            "not a pass/fail gate. A high score on an unrelated-sounding category "
            "is common; a low score doesn't guarantee the theme is fresh either. "
            "Read the actual top names and judge whether the candidate would feel "
            "redundant next to them."
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
