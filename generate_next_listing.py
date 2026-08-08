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
MODEL = "nvidia/nemotron-nano-9b-v2:free"
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

    return f"""You are drafting Etsy SEO metadata for DynoDesignsStore, a digital art \
print shop selling oil-painting-style wall art as instant digital downloads. \
The image prompt is already finalised — do not change it. Your job is the \
metadata only.

Concept: {task['concept_title']}{series_line}{sub_line}

Finalised image prompt (for context only):
{task['base_prompt']}

Produce STRICT JSON only — no markdown fences, no preamble — with these keys:

"title"
- Under 140 characters. Use every character — unused space is a missed keyword.
- Lead with the strongest searchable phrase (what a buyer would actually type).
- Structure: [Primary keyword phrase] | [Style/mood descriptor] | [Product type] | [Occasion or use]
- Example structure: "Leo Zodiac Wall Art Print | Celestial Star Sign Decor | Oil Painting Style | Digital Download"
- Include the specific variant name if one is given.

"tags"
- Exactly 13 tags. Each tag must be under 20 characters including spaces.
- Every tag must be a multi-word phrase — single-word tags are too broad to drive traffic.
- Tags must overlap with words already used in the title and description (Etsy rewards consistency).
- Cover all of these categories across the 13 tags:
  * 3 theme/style tags (e.g. "celestial wall art", "zodiac art print", "boho home decor")
  * 2 room/placement tags (e.g. "bedroom wall decor", "living room art")
  * 2 gift occasion tags (e.g. "gift for her", "housewarming gift")
  * 2 format tags (e.g. "digital download", "printable wall art")
  * 2 art-type tags (e.g. "oil painting print", "illustrated art")
  * 2 further long-tail search phrases specific to this listing

"description"
- 280-380 words. Plain text, no markdown.
- The first 160 characters are shown as the Google search snippet — open with the \
primary keyword phrase and a compelling hook within those first 160 characters.
- Repeat the primary keyword phrase naturally 2-3 times across the description.
- Paragraph 1 (hook + keywords): Describe the artwork vividly, weaving in the top \
2-3 search phrases. Mention the style, mood, and colours.
- Paragraph 2 (buyer fit + occasion): Who this is perfect for. Include gift occasions \
("gift for her", "birthday gift", "housewarming gift") and room styles \
("boho bedroom", "maximalist gallery wall", "meditation space") relevant to this piece.
- Paragraph 3 (sizes + quality): Available print sizes: A4 (8.3x11.7in), \
A3 (11.7x16.5in), A2 (16.5x23.4in), A1 (23.4x33.1in), 5x7in, 8x10in, 11x14in, \
16x20in, 18x24in, 24x36in. Files are 300 DPI, print-ready for professional results.
- Paragraph 4 (download statement): Use the phrases "instant digital download", \
"printable wall art", and "digital print" in this paragraph. State clearly that \
no physical item is shipped — files are delivered immediately after purchase.

"suggested_displayed_price_gbp"
- A number. Singles: £9.99-£12.99. Use higher end for premium/complex artwork or \
bundle-eligible series items.

"notes_for_review"
- 1-2 sentences. Flag IP risk, tag character-count issues, or wording too close \
to another listing in this series.
"""


def call_llm(prompt):
    client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=LLM_BASE_URL)
    messages = [
        {"role": "system", "content": "You respond with valid JSON only. No markdown fences, no commentary, no text outside the JSON object."},
        {"role": "user", "content": prompt},
    ]
    last_error = None
    for attempt in range(3):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=2200,
        )
        text = response.choices[0].message.content.strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            last_error = e
            print(f"JSON parse attempt {attempt + 1} failed: {e} — retrying")
    raise last_error


def main():
    if not os.environ.get("LLM_API_KEY"):
        print("Set LLM_API_KEY in your environment first.")
        sys.exit(1)

    if not PLAN_PATH.exists():
        print(f"plan.md not found at {PLAN_PATH}. Copy your expansion plan there.")
        sys.exit(1)

    with open(PLAN_PATH) as f:
        plan_text = f.read()

    today = date.today().isoformat()
    drafted_today = set()
    if OUTPUT_DIR.exists():
        for draft_file in OUTPUT_DIR.glob(f"{today}_concept*.json"):
            try:
                with open(draft_file) as jf:
                    d = json.load(jf)
                drafted_today.add((d["_concept_num"], d.get("_sub_item")))
            except Exception:
                pass
    if drafted_today:
        print(f"Skipping tasks already drafted today: {drafted_today}")

    task = get_next_task(plan_text, skip_tasks=drafted_today)
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
