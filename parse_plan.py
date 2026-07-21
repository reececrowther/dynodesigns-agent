"""
Parses DynoDesigns_Expansion_Plan.md directly. The .md file stays the single
source of truth — no separate config to keep in sync. You keep writing
"DONE" inline the way you already do; this just reads it.
"""

import re

CONCEPT_RE = re.compile(r"^\*\*(\d+)\.\s*(.+?)\*\*\s*(.*)$")
FENCE_RE = re.compile(r"^```")
BRACKET_GROUP_RE = re.compile(r"\[([A-Z0-9 '/\-]+)\]")


def parse_concepts(md_text):
    lines = md_text.split("\n")
    concepts = []
    i = 0
    while i < len(lines):
        m = CONCEPT_RE.match(lines[i].strip())
        if m:
            num, title, marker = m.group(1), m.group(2).strip(), m.group(3).strip()

            # find the next fenced code block for the prompt
            prompt_lines = []
            j = i + 1
            while j < len(lines) and not FENCE_RE.match(lines[j].strip()):
                j += 1
            if j < len(lines):  # found opening fence
                j += 1
                while j < len(lines) and not FENCE_RE.match(lines[j].strip()):
                    prompt_lines.append(lines[j])
                    j += 1
            prompt = " ".join(l.strip() for l in prompt_lines if l.strip())
            prompt = re.sub(r"\s+", " ", prompt).strip()

            concepts.append({
                "num": int(num),
                "title": title,
                "marker": marker,
                "prompt": prompt,
                "line_index": i,
            })
        i += 1
    return concepts


def sub_items_for(concept):
    """If the prompt has a bracket group like [A / B / C], this is a series."""
    match = BRACKET_GROUP_RE.search(concept["prompt"])
    if not match:
        return None
    return [s.strip() for s in match.group(1).split("/")]


def done_sub_items_for(concept):
    """Extract names listed after 'DONE:' in an IN PROGRESS marker."""
    m = re.search(r"DONE:\s*(.+?)\)?\s*$", concept["marker"], re.IGNORECASE)
    if not m:
        return []
    return [s.strip().upper() for s in m.group(1).split(",")]


def get_status(concept):
    marker = concept["marker"].upper()
    if "IN PROGRESS" in marker:
        return "partial"
    if "DONE" in marker:
        return "done"
    return "pending"


def get_next_task(md_text):
    """
    Returns the next actionable task, or None if everything is done.
    For series concepts, returns the next undone sub-item specifically.
    """
    concepts = parse_concepts(md_text)
    for c in concepts:
        status = get_status(c)
        if status == "done":
            continue

        sub_items = sub_items_for(c)

        if status == "partial":
            done = done_sub_items_for(c)
            remaining = [s for s in sub_items if s.upper() not in done] if sub_items else []
            if remaining:
                return {
                    "concept_num": c["num"],
                    "concept_title": c["title"],
                    "sub_item": remaining[0],
                    "remaining_count": len(remaining),
                    "total_sub_items": len(sub_items) if sub_items else None,
                    "base_prompt": c["prompt"],
                }
            continue  # partial but somehow nothing remaining — treat as done, move on

        # status == "pending"
        if sub_items:
            return {
                "concept_num": c["num"],
                "concept_title": c["title"],
                "sub_item": sub_items[0],
                "remaining_count": len(sub_items),
                "total_sub_items": len(sub_items),
                "base_prompt": c["prompt"],
            }
        else:
            return {
                "concept_num": c["num"],
                "concept_title": c["title"],
                "sub_item": None,
                "remaining_count": 1,
                "total_sub_items": 1,
                "base_prompt": c["prompt"],
            }
    return None


if __name__ == "__main__":
    with open("plan.md") as f:
        text = f.read()
    concepts = parse_concepts(text)
    print(f"Parsed {len(concepts)} concepts.\n")
    for c in concepts:
        status = get_status(c)
        tag = f"[{status}]"
        sub = sub_items_for(c)
        extra = f" ({len(sub)} sub-items)" if sub else ""
        print(f"{tag:10} #{c['num']:2} {c['title']}{extra}")

    print("\n--- NEXT TASK ---")
    task = get_next_task(text)
    print(task)
