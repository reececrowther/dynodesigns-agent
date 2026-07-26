#!/usr/bin/env python3
"""
Builds docs/index.html from the most recent file in drafts/.
GitHub Pages serves docs/ as a static site — no server involved.
"""

import json
import os
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
  .done-btn {{ background: #c0392b; color: white; border: none; padding: 12px 20px;
              border-radius: 8px; font-size: 1rem; cursor: pointer; margin-top: 24px;
              width: 100%; }}
  .done-btn:active {{ opacity: 0.8; }}
  .done-btn:disabled {{ background: #aaa; cursor: default; }}
  #done-status {{ margin-top: 10px; font-size: 0.9rem; color: #8a7d6a; }}
  #token-box {{ background: #fff; border-radius: 12px; padding: 16px;
               box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-top: 12px; display: none; }}
  #token-box p {{ font-size: 0.85rem; color: #8a7d6a; margin: 0 0 8px 0; }}
  #token-box input {{ width: 100%; padding: 8px 10px; border: 1px solid #d9cfc4;
                      border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; }}
  #token-box input:focus {{ outline: 2px solid #3d5a3d; }}
  .clear-token {{ font-size: 0.78rem; color: #a08d6f; background: none; border: none;
                  cursor: pointer; padding: 0; margin-top: 6px; text-decoration: underline; }}
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
    <button onclick="copyTags()" style="margin-top:12px;">Copy all tags (comma separated)</button>
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

  <button class="done-btn" id="done-btn" onclick="markDone()">Mark as Live on Etsy</button>

  <div id="token-box">
    <p>Paste a GitHub Personal Access Token with <strong>workflow</strong> scope.<br>
       It is saved in your browser only and sent nowhere except GitHub.</p>
    <input type="password" id="token-input" placeholder="ghp_…" />
    <div style="display:flex; gap:8px; margin-top:8px;">
      <button onclick="submitToken()">Save &amp; confirm</button>
      <button onclick="hideTokenBox()" style="background:#999;">Cancel</button>
    </div>
  </div>

  <div id="done-status"></div>
  <button class="clear-token" id="clear-btn" onclick="clearToken()" style="display:none;">Forget saved token</button>

  <div class="howto">
    Tap "Mark as Live on Etsy" once the listing is published. You will be asked
    for a GitHub token the first time — create one at GitHub → Settings →
    Developer settings → Personal access tokens → Tokens (classic), tick the
    <code>workflow</code> scope.
  </div>

  <script>
    const CONCEPT_NUM = "{concept_num}";
    const SUB_ITEM = "{sub_item_js}";
    const REPO = "reececrowther/dynodesigns-agent";
    const TAGS = {tags_js};
    const BAKED_TOKEN = "{pages_token}";

    if (BAKED_TOKEN) {{
      // Token is embedded at build time — hide the manual input UI entirely
      document.getElementById('token-box').style.display = 'none';
      document.getElementById('clear-btn').style.display = 'none';
    }} else if (localStorage.getItem('gh_token')) {{
      document.getElementById('clear-btn').style.display = 'inline';
    }}

    function copyText(id) {{
      navigator.clipboard.writeText(document.getElementById(id).innerText);
    }}

    function copyTags() {{
      navigator.clipboard.writeText(TAGS.join(', '));
    }}

    function hideTokenBox() {{
      document.getElementById('token-box').style.display = 'none';
      document.getElementById('token-input').value = '';
    }}

    function clearToken() {{
      localStorage.removeItem('gh_token');
      document.getElementById('clear-btn').style.display = 'none';
      document.getElementById('done-status').textContent = 'Token cleared.';
    }}

    function markDone() {{
      const token = BAKED_TOKEN || localStorage.getItem('gh_token');
      if (!token) {{
        document.getElementById('token-box').style.display = 'block';
        document.getElementById('token-input').focus();
        return;
      }}
      triggerWorkflow(token);
    }}

    function submitToken() {{
      const token = document.getElementById('token-input').value.trim();
      if (!token) return;
      localStorage.setItem('gh_token', token);
      document.getElementById('clear-btn').style.display = 'inline';
      hideTokenBox();
      triggerWorkflow(token);
    }}

    async function triggerWorkflow(token) {{
      const status = document.getElementById('done-status');
      const btn = document.getElementById('done-btn');
      btn.disabled = true;
      status.textContent = 'Triggering workflow…';

      const res = await fetch(
        `https://api.github.com/repos/${{REPO}}/actions/workflows/mark-done.yml/dispatches`,
        {{
          method: 'POST',
          headers: {{
            'Authorization': `Bearer ${{token}}`,
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
          }},
          body: JSON.stringify({{ ref: 'main', inputs: {{ concept_num: CONCEPT_NUM, sub_item: SUB_ITEM }} }}),
        }}
      );

      if (res.status === 204) {{
        status.textContent = "Done! plan.md will be updated and tomorrow's draft will move to the next concept.";
      }} else {{
        const data = await res.json().catch(() => ({{}}));
        status.textContent = 'Error: ' + (data.message || res.status) + '. Token cleared — try again.';
        localStorage.removeItem('gh_token');
        document.getElementById('clear-btn').style.display = 'none';
        btn.disabled = false;
      }}
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
    tags_js = json.dumps(d["tags"])

    html = TEMPLATE.format(
        title=d["title"],
        concept_num=d["_concept_num"],
        concept_title=d["_concept_title"],
        sub_item_str=sub_item_str,
        sub_item_js=sub_item or "",
        image_prompt=d["_image_prompt"],
        tags_html=tags_html,
        tags_js=tags_js,
        description="<br><br>".join(p.strip() for p in d["description"].split("\n") if p.strip()),
        price=d["suggested_displayed_price_gbp"],
        notes=d["notes_for_review"],
        sub_item_hint=sub_item_hint,
        pages_token=os.environ.get("PAGES_GITHUB_TOKEN", ""),
    )

    DOCS_DIR.mkdir(exist_ok=True)
    with open(DOCS_DIR / "index.html", "w") as f:
        f.write(html)

    print(f"Built docs/index.html from {latest.name}")


if __name__ == "__main__":
    main()
