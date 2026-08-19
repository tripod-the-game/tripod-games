#!/usr/bin/env python3
"""Helper for the new-games skill: reads puzzle history and verifies candidates.

Subcommands:
  context  -- scan the repo's existing puzzles and print a JSON summary of
              recent categories/words to avoid, plus the next unused dates.
  verify   -- check one candidate game (JSON on argv) against the triangle
              constraint and against recent word/category usage.
  pattern  -- look up real dictionary words matching a letter pattern
              (e.g. size 5, pattern "c___t" -> all 5-letter words starting
              with c and ending in t). Use this to browse real candidates
              for a corner-letter slot instead of guessing from memory.
  search   -- given a JSON list of candidate words you believe fit a theme,
              find every valid triangle among the ones that are real
              dictionary words (checked against data/words{4,5}.txt), and
              flag any supplied words that aren't in the dictionary.

The dictionary (data/words4.txt, data/words5.txt) is a bundled, frequency-
filtered list of common English words (not proper nouns, not Scrabble-only
obscurities) -- see README-ish note in cmd_pattern/cmd_search docstrings.
"""
import argparse
import glob
import itertools
import json
import os
import re
import sys
from datetime import datetime, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
WORD_REUSE_MIN_DAYS = 20  # observed norm in repo history: reused words are usually 20+ days apart
RECURRING_CATEGORY_MIN_USES = 2  # categories used >=2 times are treated as intentional recurring buckets


def load_dictionary(size):
    path = os.path.join(DATA_DIR, f"words{size}.txt")
    with open(path) as f:
        return [w.strip() for w in f if w.strip()]


def find_triangles(words):
    """Return every (wordOne, wordTwo, wordThree) triple in `words` that
    satisfies the triangle constraint. O(n^2) apex-matching, not O(n^3)."""
    words = list(dict.fromkeys(words))  # dedupe, keep order
    by_first = {}
    for w in words:
        by_first.setdefault(w[0], []).append(w)

    results = []
    for w1, w2 in itertools.permutations(words, 2):
        if w1[-1] != w2[0]:
            continue
        for w3 in by_first.get(w1[0], []):
            if w3 in (w1, w2):
                continue
            if w2[-1] == w3[-1]:
                results.append((w1, w2, w3))
    return results


def load_all_games():
    files = [
        f for f in glob.glob(os.path.join(REPO_ROOT, "20*", "*", "*.json"))
        if os.path.basename(f) != "index.json"
    ]
    games = []
    for f in sorted(files):
        base = os.path.splitext(os.path.basename(f))[0]
        try:
            date = datetime.strptime(base, "%m%d%y")
        except ValueError:
            continue
        with open(f) as fh:
            data = json.load(fh)
        games.append((date, base, data))
    games.sort(key=lambda x: x[0])
    return games


def cmd_context(args):
    games = load_all_games()
    if not games:
        print(json.dumps({"error": "no existing puzzle files found"}))
        return

    latest_date = games[-1][0]

    # next N unused calendar dates after the latest one on record
    next_dates = []
    d = latest_date + timedelta(days=1)
    while len(next_dates) < args.count:
        mmddyy = d.strftime("%m%d%y")
        next_dates.append({
            "date": mmddyy,
            "weekday": d.strftime("%A"),
            "path": f"{d.strftime('%Y')}/{d.strftime('%m')}/{mmddyy}.json",
        })
        d += timedelta(days=1)

    # category usage: every category ever used, with count and most recent date
    category_info = {}
    for date, base, data in games:
        cat = data.get("category")
        if cat not in category_info:
            category_info[cat] = {"count": 0, "last_used": None, "last_used_days_ago": None}
        category_info[cat]["count"] += 1
        category_info[cat]["last_used"] = base
        category_info[cat]["last_used_days_ago"] = (latest_date - date).days

    recurring_categories = {
        cat: info for cat, info in category_info.items()
        if info["count"] >= RECURRING_CATEGORY_MIN_USES
    }
    one_off_categories = sorted(cat for cat, info in category_info.items() if info["count"] == 1)

    # word usage: most recent date each word appeared
    word_last_used = {}
    for date, base, data in games:
        for w in (data.get("wordOne"), data.get("wordTwo"), data.get("wordThree")):
            if w:
                word_last_used[w] = base  # sorted ascending, so last write wins = most recent

    today_ish = latest_date
    word_recency = {
        w: {
            "last_used": last,
            "days_ago": (today_ish - datetime.strptime(last, "%m%d%y")).days,
        }
        for w, last in word_last_used.items()
    }

    out = {
        "latest_date_on_record": latest_date.strftime("%m%d%y"),
        "total_games": len(games),
        "next_unused_dates": next_dates,
        "word_reuse_min_days_norm": WORD_REUSE_MIN_DAYS,
        "recurring_categories": recurring_categories,
        "one_off_categories_used_before": one_off_categories,
        "word_last_used": word_recency,
        "note": (
            "Avoid 'one_off_categories_used_before' entirely for new candidates "
            "unless deliberately reviving one after a long gap. "
            "'recurring_categories' are OK to reuse only in their established pattern "
            "(e.g. 'No Category Sunday' only on a Sunday date). "
            "For any word you plan to use, check word_last_used[word].days_ago -- "
            "if it's under word_reuse_min_days_norm, pick a different word."
        ),
    }
    print(json.dumps(out, indent=2))


def cmd_verify(args):
    try:
        candidate = json.loads(args.json)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "errors": [f"invalid JSON: {e}"]}))
        sys.exit(1)

    errors = []
    warnings = []

    category = candidate.get("category")
    size = candidate.get("size", 5)
    w1 = candidate.get("wordOne", "")
    w2 = candidate.get("wordTwo", "")
    w3 = candidate.get("wordThree", "")

    if not category:
        errors.append("missing category")
    if size not in (4, 5):
        errors.append(f"size must be 4 or 5, got {size!r}")
    for name, w in (("wordOne", w1), ("wordTwo", w2), ("wordThree", w3)):
        if not w:
            errors.append(f"missing {name}")
        elif not w.islower() or not w.isalpha():
            errors.append(f"{name} ({w!r}) must be lowercase alphabetic")
        elif len(w) != size:
            errors.append(f"{name} ({w!r}) has length {len(w)}, expected {size}")

    if not errors:
        apex_ok = w1[-1] == w2[0]
        bl_ok = w1[0] == w3[0]
        br_ok = w2[-1] == w3[-1]
        constraints = {
            "apex (wordOne[last] == wordTwo[first])": {
                "expected": f"{w1[-1]!r} == {w2[0]!r}", "ok": apex_ok,
            },
            "bottom-left (wordOne[first] == wordThree[first])": {
                "expected": f"{w1[0]!r} == {w3[0]!r}", "ok": bl_ok,
            },
            "bottom-right (wordTwo[last] == wordThree[last])": {
                "expected": f"{w2[-1]!r} == {w3[-1]!r}", "ok": br_ok,
            },
        }
        if not (apex_ok and bl_ok and br_ok):
            errors.append("triangle constraint violated")
    else:
        constraints = None

    if w1 == w2 or w2 == w3 or w1 == w3:
        errors.append("wordOne/wordTwo/wordThree must all be distinct")

    games = load_all_games()
    latest_date = games[-1][0] if games else None

    category_counts = {}
    word_last_used = {}
    for date, base, data in games:
        c = data.get("category")
        category_counts[c] = category_counts.get(c, 0) + 1
        for w in (data.get("wordOne"), data.get("wordTwo"), data.get("wordThree")):
            if w:
                word_last_used[w] = base

    if category in category_counts:
        warnings.append(
            f"category {category!r} has already been used {category_counts[category]}x before "
            f"(ok only if this is an intentional recurring bucket)"
        )

    for name, w in (("wordOne", w1), ("wordTwo", w2), ("wordThree", w3)):
        if w in word_last_used and latest_date:
            last = datetime.strptime(word_last_used[w], "%m%d%y")
            days_ago = (latest_date - last).days
            if days_ago < WORD_REUSE_MIN_DAYS:
                warnings.append(
                    f"{name} ({w!r}) was last used {word_last_used[w]}, only {days_ago} days ago "
                    f"(norm is {WORD_REUSE_MIN_DAYS}+ days)"
                )

    print(json.dumps({
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "constraints": constraints,
    }, indent=2))
    if errors:
        sys.exit(1)


def cmd_pattern(args):
    size = args.size
    pattern = args.pattern
    if len(pattern) != size:
        print(json.dumps({"error": f"pattern length {len(pattern)} != size {size}"}))
        sys.exit(1)

    regex = "^" + "".join("." if c in "_." else re.escape(c) for c in pattern.lower()) + "$"
    rx = re.compile(regex)

    dictionary = load_dictionary(size)
    matches = [w for w in dictionary if rx.match(w)]
    print(json.dumps({
        "pattern": pattern,
        "size": size,
        "match_count": len(matches),
        "matches": matches,
    }, indent=2))


def cmd_search(args):
    try:
        candidates = json.loads(args.words)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}"}))
        sys.exit(1)

    size = args.size
    dictionary = set(load_dictionary(size))

    candidates = [w.lower() for w in candidates]
    valid = [w for w in candidates if len(w) == size and w in dictionary]
    not_in_dictionary = [w for w in candidates if w not in valid]

    triangles = find_triangles(valid)

    games = load_all_games()
    latest_date = games[-1][0] if games else None
    word_last_used = {}
    for date, base, data in games:
        for w in (data.get("wordOne"), data.get("wordTwo"), data.get("wordThree")):
            if w:
                word_last_used[w] = base

    def recency_flag(w):
        if w in word_last_used and latest_date:
            days_ago = (latest_date - datetime.strptime(word_last_used[w], "%m%d%y")).days
            if days_ago < WORD_REUSE_MIN_DAYS:
                return f"used {days_ago}d ago"
        return None

    results = []
    for w1, w2, w3 in triangles:
        flags = {w: recency_flag(w) for w in (w1, w2, w3) if recency_flag(w)}
        results.append({
            "wordOne": w1, "wordTwo": w2, "wordThree": w3,
            "recency_warnings": flags or None,
        })

    print(json.dumps({
        "size": size,
        "candidates_supplied": len(candidates),
        "candidates_not_in_dictionary": not_in_dictionary,
        "triangle_count": len(results),
        "triangles": results,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_context = sub.add_parser("context", help="summarize puzzle history for planning new games")
    p_context.add_argument("--count", type=int, default=3, help="how many next unused dates to suggest")
    p_context.set_defaults(func=cmd_context)

    p_verify = sub.add_parser("verify", help="verify one candidate game JSON")
    p_verify.add_argument("json", help="candidate game as a JSON string")
    p_verify.set_defaults(func=cmd_verify)

    p_pattern = sub.add_parser("pattern", help="look up real words matching a letter pattern")
    p_pattern.add_argument("size", type=int, choices=[4, 5])
    p_pattern.add_argument("pattern", help="e.g. c___t (use _ as wildcard)")
    p_pattern.set_defaults(func=cmd_pattern)

    p_search = sub.add_parser("search", help="find valid triangles among a list of candidate words")
    p_search.add_argument("size", type=int, choices=[4, 5])
    p_search.add_argument("words", help="JSON array of candidate words, e.g. '[\"pass\",\"shot\",\"post\"]'")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
