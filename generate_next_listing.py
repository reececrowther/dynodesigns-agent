#!/usr/bin/env python3
"""
Reads plan.md directly (no separate config), finds the next undone task,
and drafts the Etsy metadata that's missing — title, tags, description,
price. It does NOT invent the image prompt; your plan already has those.

Requires: LLM_API_KEY environment variable.
Run: python3 generate_next_listing.py
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

from parse_plan import get_next_task

try:
    from openai import OpenAI
except ImportError:
    print("Missing dependency. Run: pip install openai --break-system-packages")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
PLAN_PATH = BASE_DIR / "plan.md"
OUTPUT_DIR = BASE_DIR / "drafts"

# --- Provider config ---
# OpenRouter (current):
LLM_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"
# To switch back to Groq, comment the two lines above and uncomment these:
# LLM_BASE_URL = "https://api.groq.com/openai/v1"
# MODEL = "llama-3.3-70b-versatile"
# ----------------------


def build_prompt(task):
    sub_line = f"\nSpecific variant for this listing: {task['sub_item']}" if task["sub_item"] else ""
    series_line = (
        f"\nThis is part of a {task['total_sub_items']}-listing series "
        f"({task['remaining_count']} remaining including this one)."
        if task["total_sub_items"] and task["total_sub_items"] > 1 else ""
    )

    return f"""You are drafting Etsy listing metadata for DynoDesignsStore, a digital \
print shop. The image prompt below is already finalised — do not change or \
rewrite it. Your job is only the metadata around it.

Concept: {task['concept_title']}{series_line}{sub_line}

Finalised image prompt (for context only):
{task['base_prompt']}

Produce STRICT JSON only, no markdown fences, no preamble, with these keys:
- "title": Etsy-optimised title, under 140 characters, incorporating the specific \
variant if one is given
- "tags": array of exactly 13 Etsy tags, each under 20 characters, no duplicates
- "description": 2-3 short paragraphs, plain text, no markdown
- "suggested_displayed_price_gbp": a number, informed by the plan's £9.99-12.99 \
range for singles (use judgement for bundle-eligible series items)
- "notes_for_review": 1-2 sentences flagging anything worth double-checking \
(e.g. wording closeness to a previous listing in this series)
"""


def call_llm(prompt):
    client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=LLM_BASE_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
    )
    text = response.choices[0].message.content.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def main():
    if not os.environ.get("LLM_API_KEY"):
        print("Set LLM_API_KEY in your environment first.")
        sys.exit(1)

    if not PLAN_PATH.exists():
        print(f"plan.md not found at {PLAN_PATH}. Copy your expansion plan there.")
        sys.exit(1)

    with open(PLAN_PATH) as f:
        plan_text = f.read()

    task = get_next_task(plan_text)
    if task is None:
        print("No pending tasks found — plan.md shows everything as DONE.")
        sys.exit(0)

    label = f"#{task['concept_num']} {task['concept_title']}"
    if task["sub_item"]:
        label += f" — {task['sub_item']}"
    print(f"Next task: {label}")
    if task["total_sub_items"] and task["total_sub_items"] > 1:
        print(f"({task['remaining_count']} of {task['total_sub_items']} remaining in this series)")

    prompt = build_prompt(task)
    result = call_llm(prompt)
    result["_concept_num"] = task["concept_num"]
    result["_concept_title"] = task["concept_title"]
    result["_sub_item"] = task["sub_item"]

    # Substitute the chosen variant into the bracket group for the actual image prompt.
    if task["sub_item"]:
        result["_image_prompt"] = re.sub(r"\[[^\]]+\]", task["sub_item"], task["base_prompt"], count=1)
    else:
        result["_image_prompt"] = task["base_prompt"]

    OUTPUT_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    safe_sub = f"_{task['sub_item'].replace(' ', '-')}" if task["sub_item"] else ""
    out_path = OUTPUT_DIR / f"{today}_concept{task['concept_num']:02d}{safe_sub}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nDraft saved to: {out_path}")
    print(f"Title: {result['title']}")
    print(f"Image prompt to use in Midjourney:\n{result['_image_prompt']}")
    print(f"Suggested price: £{result['suggested_displayed_price_gbp']}")
    print(f"Review notes: {result['notes_for_review']}")
    print(f"\nWhen live on Etsy, run: python3 mark_done.py {task['concept_num']}"
          + (f' "{task["sub_item"]}"' if task["sub_item"] else ""))


if __name__ == "__main__":
    main()
