#!/usr/bin/env python3
"""
Builds docs/index.html from the most recent file in drafts/.
GitHub Pages serves docs/ as a static site — no server involved.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
DRAFTS_DIR = BASE_DIR / "drafts"
DOCS_DIR = BASE_DIR / "docs"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DynoDesigns — Next Listing</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 640px;
         margin: 0 auto; padding: 24px 16px; background: #faf8f5; color: #2b2620; }}
  h1 {{ font-size: 1.3rem; margin-bottom: 4px; }}
  .meta {{ color: #8a7d6a; font-size: 0.9rem; margin-bottom: 24px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 18px; margin-bottom: 16px;
           box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;
            color: #a08d6f; margin-bottom: 6px; }}
  .value {{ font-size: 1rem; line-height: 1.5; }}
  .tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .tag {{ background: #f0e8dc; padding: 4px 10px; border-radius: 999px; font-size: 0.85rem; }}
  .price {{ font-size: 1.4rem; font-weight: 600; color: #3d5a3d; }}
  .notes {{ background: #fdf3e3; border-left: 3px solid #d9a441; padding: 10px 14px;
            border-radius: 6px; }}
  button {{ background: #3d5a3d; color: white; border: none; padding: 8px 14px;
            border-radius: 8px; font-size: 0.85rem; cursor: pointer; margin-top: 8px; }}
  button:active {{ opacity: 0.8; }}
  code {{ font-size: 0.85rem; background: #f0e8dc; padding: 2px 6px; border-radius: 4px; }}
  .howto {{ font-size: 0.85rem; color: #8a7d6a; margin-top: 32px; }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">Concept #{concept_num} — {concept_title}{sub_item_str}</div>

  <div class="card">
    <div class="label">Image prompt (for Midjourney)</div>
    <div class="value" id="prompt">{image_prompt}</div>
    <button onclick="copyText('prompt')">Copy prompt</button>
  </div>

  <div class="card">
    <div class="label">Etsy tags (13)</div>
    <div class="tags">{tags_html}</div>
  </div>

  <div class="card">
    <div class="label">Description</div>
    <div class="value">{description}</div>
  </div>

  <div class="card">
    <div class="label">Suggested displayed price</div>
    <div class="price">£{price}</div>
  </div>

  <div class="notes">{notes}</div>

  <div class="howto">
    When this is live on Etsy, go to Actions → "Mark Listing Done" in the
    repo, run it with concept number <code>{concept_num}</code>{sub_item_hint}.
  </div>

  <script>
    function copyText(id) {{
      navigator.clipboard.writeText(document.getElementById(id).innerText);
    }}
  </script>
</body>
</html>
"""


def main():
    if not DRAFTS_DIR.exists():
        print("No drafts folder yet.")
        return

    draft_files = sorted(DRAFTS_DIR.glob("*.json"))
    if not draft_files:
        print("No drafts found.")
        return

    latest = draft_files[-1]
    with open(latest) as f:
        d = json.load(f)

    sub_item = d.get("_sub_item")
    sub_item_str = f" — {sub_item}" if sub_item else ""
    sub_item_hint = f' and sub-item "{sub_item}"' if sub_item else ""

    tags_html = "".join(f'<span class="tag">{t}</span>' for t in d["tags"])

    html = TEMPLATE.format(
        title=d["title"],
        concept_num=d["_concept_num"],
        concept_title=d["_concept_title"],
        sub_item_str=sub_item_str,
        image_prompt=d["_image_prompt"],
        tags_html=tags_html,
        description="<br><br>".join(p.strip() for p in d["description"].split("\n") if p.strip()),
        price=d["suggested_displayed_price_gbp"],
        notes=d["notes_for_review"],
        sub_item_hint=sub_item_hint,
    )

    DOCS_DIR.mkdir(exist_ok=True)
    with open(DOCS_DIR / "index.html", "w") as f:
        f.write(html)

    print(f"Built docs/index.html from {latest.name}")


if __name__ == "__main__":
    main()
