# DynoDesigns Listing Agent

Runs entirely on GitHub — no server, no database, no Vercel. `plan.md`
stays the single file you already maintain by hand; the agent reads and
writes to it directly.

## What runs where

- **"Generate Daily Draft"** workflow — runs on a schedule (default 8am
  UTC), finds the next undone concept or series item in `plan.md`, drafts
  the missing Etsy metadata (title, tags, description, price), and
  rebuilds `docs/index.html` with the result. Commits both back to the repo.
- **GitHub Pages**, serving `docs/index.html` — this is the "nice webpage."
  Static, free, no server.
- **"Mark Listing Done"** workflow — you trigger this manually (from the
  GitHub app on your phone or the Actions tab) once a listing is actually
  live on Etsy. Writes `DONE` back into `plan.md` in the same style you'd
  type by hand.

## One-time setup

1. **Create a repo** (private is fine) and push these files to it,
   including `plan.md` and the `.github/workflows/` folder.
2. **Add your API key as a secret**: repo Settings → Secrets and
   variables → Actions → New repository secret →
   name it `GOOGLE_API_KEY`. Get a free key at aistudio.google.com.
3. **Enable Pages**: repo Settings → Pages → Source: "Deploy from a
   branch" → branch `main`, folder `/docs`. GitHub gives you a URL like
   `https://yourusername.github.io/dynodesigns-agent/`.
4. **Check the workflow permissions**: repo Settings → Actions → General
   → Workflow permissions → set to "Read and write permissions" (needed
   so the Action can commit back to the repo).

That's it — no deploy step, no build pipeline.

## Daily use

1. Each morning, visit your Pages URL (bookmark it, or add to your phone's
   home screen — it'll feel like an app).
2. Review the draft: check the `notes_for_review` line, generate the image
   in Midjourney using the printed prompt, upload to Etsy with the
   suggested title/tags/description/price.
3. Open the GitHub app → your repo → Actions → "Mark Listing Done" → Run
   workflow → enter the concept number (and sub-item name if it's a series
   item like a moon phase or zodiac sign).
4. Tomorrow's draft appears automatically before you even open the page.

## Before your first real run

- **Check concept #14 (moon phases) against reality.** I couldn't tell
  from "made it to 15" whether WAXING GIBBOUS is actually live yet, so
  `plan.md` here is exactly what you uploaded, untouched. If it's live,
  run "Mark Listing Done" with concept `14` and sub-item `WAXING GIBBOUS`
  before the first daily draft runs, or it'll draft that one again.
- Test the first run manually via workflow_dispatch (Actions tab → "Run
  workflow") rather than waiting for the schedule, so you can check the
  output before trusting it unattended.

## What this still won't do (on purpose)

- Publish to Etsy directly, or judge trademark/IP closeness to Minecraft
  or Stardew Valley — both need your judgement, not an agent's.
- Touch existing listing prices or the permanent-discount removal —
  those are one-off decisions, not a repeatable daily loop.
