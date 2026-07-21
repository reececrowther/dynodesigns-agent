#!/usr/bin/env python3
"""
Marks a concept (or a specific sub-item of a series) as DONE directly in
plan.md, using the same inline style you already write by hand. Run this
only after the listing is actually live on Etsy — a draft existing doesn't
mean it's done.

Usage:
  python3 mark_done.py 25                  # simple concept
  python3 mark_done.py 14 "WAXING GIBBOUS" # one item in a series
"""

import re
import sys
from pathlib import Path

from parse_plan import parse_concepts, sub_items_for, done_sub_items_for

PLAN_PATH = Path(__file__).parent / "plan.md"


def main():
    if len(sys.argv) not in (2, 3):
        print('Usage: python3 mark_done.py <concept_num> ["SUB ITEM NAME"]')
        sys.exit(1)

    concept_num = int(sys.argv[1])
    sub_item = sys.argv[2].upper() if len(sys.argv) == 3 else None

    with open(PLAN_PATH) as f:
        lines = f.read().split("\n")

    plan_text = "\n".join(lines)
    concepts = parse_concepts(plan_text)
    concept = next((c for c in concepts if c["num"] == concept_num), None)
    if concept is None:
        print(f"Concept #{concept_num} not found in plan.md")
        sys.exit(1)

    idx = concept["line_index"]
    line = lines[idx]
    sub_items = sub_items_for(concept)

    if sub_items and sub_item:
        already_done = done_sub_items_for(concept)
        if sub_item in already_done:
            print(f"'{sub_item}' is already marked done for #{concept_num}.")
            sys.exit(0)
        already_done.append(sub_item)

        title_part = line.split("**")[1]  # already includes "14. Moon Phases..."
        if set(already_done) >= set(s.upper() for s in sub_items):
            new_line = f"**{title_part}** DONE"
        else:
            done_str = ", ".join(already_done)
            new_line = f"**{title_part}** IN PROGRESS (DONE: {done_str})"

        lines[idx] = new_line
        print(f"Updated #{concept_num}: {len(already_done)}/{len(sub_items)} done.")

    else:
        if "DONE" in concept["marker"].upper():
            print(f"#{concept_num} is already marked done.")
            sys.exit(0)
        title_part = line.split("**")[1]  # already includes "25. Fox in..."
        lines[idx] = f"**{title_part}** DONE"
        print(f"Marked #{concept_num} ({concept['title']}) as DONE.")

    with open(PLAN_PATH, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
