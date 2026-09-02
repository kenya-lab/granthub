# Grant AI — search, index, and draft grant applications

Starter app for finding grants and drafting applications, built around
Innervision Arts Academy first (easy to extend to Dream Girl Machine,
EdgeCTRL, or Sensory Studios clients later — see "Adding another
project/org" below).

## What's here

```
grant-ai/
  config/org_profile.json   <- the knowledge base every draft pulls from. FILL THIS IN FIRST.
  src/db.py                 <- SQLite schema + helpers (opportunities, drafts)
  src/search_grants_gov.py  <- pulls live federal opportunities (grants.gov API, free)
  src/search_web.py         <- for funders with no API (LA County Arts Commission, Adobe,
                                Disney) — designed to be driven by Claude Code's web search
  src/draft.py               <- Claude-powered drafting engine
  src/cli.py                 <- command line to run everything
  data/grants.db              <- created on first run
```

## Setup

```bash
cd grant-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste your Anthropic API key in
export $(cat .env | xargs)   # or use direnv/dotenv however you prefer
```

## Step 1 — fill in the org profile

Open `config/org_profile.json` and replace every `"REPLACE ME"` with real
detail about Innervision Arts Academy: mission, programs, budget, past
outcomes, leadership bios, 501(c)(3)/fiscal sponsor status. **This is the
highest-leverage step** — the quality of every drafted answer depends on how
complete and specific this file is. Vague profile in, vague drafts out.

## Step 2 — pull in opportunities

```bash
cd src
python cli.py search-federal      # pulls current grants.gov matches (NEA, etc.)
```

Everything else — named foundations, Adobe/Disney corporate giving, CDFIs,
LA City Council district discretionary funds, and LA County Board of
Supervisors district funds — has no public search API. Open this whole
`grant-ai/` folder in **Claude Code** and point it at
`config/search_sources.json`, which lists each category with search queries
and notes (e.g. for CDFIs, only log genuine grant/technical-assistance
programs — most CDFI products are loans, not grants, and those are a
different kind of decision). Before running the council-district searches,
fill in the `location` section of `org_profile.json` so it searches the
right district. Have Claude Code call `add_manual_opportunity()` in
`search_web.py` for each real result it finds, tagging `funder_category` so
you can filter by type later. Ask it to repeat this monthly — these
categories mostly run on annual/rolling cycles rather than grants.gov's
constant churn.

## Step 3 — review and triage

```bash
python cli.py list                 # see everything indexed
python cli.py list new             # just new, un-triaged matches
python cli.py show <opportunity_id>
python cli.py status <opportunity_id> reviewing   # or: drafting, submitted, skipped, awarded
```

## Step 4 — draft answers

```bash
python cli.py draft <opportunity_id> "Describe your organization's mission and the population you serve." 250
```

This pulls the org profile + the opportunity's details, drafts an answer in
Claude's voice grounded only in facts you've actually entered, and — if the
profile is missing something it needed — tells you exactly what to add
instead of making it up.

## Next steps to build out in Claude Code

- **Real UI**: turn the CLI into a small dashboard (Flask/FastAPI + a simple
  frontend, or a Next.js app) so opportunities and drafts are easier to
  browse than the command line.
- **Scheduling**: wire `search-federal` and the web-search step to run
  automatically (cron, or a Claude Code scheduled task) and notify you (email/
  Slack) when something new and well-matched shows up.
- **Match scoring**: add a step that scores each opportunity against your
  profile (amount range, eligibility, deadline feasibility) so `list` can be
  sorted by fit instead of just deadline.
- **More orgs**: duplicate `org_profile.json` per project (e.g.
  `org_profile_dgm.json` for Dream Girl Machine) and add an `--org` flag
  throughout so one install can manage all your organizations' pipelines.
- **Export**: add a command that exports a finished draft to `.docx` for
  submission portals that don't take pasted text.

## Notes on the grants.gov integration

The `search2` endpoint is public and free, no key required, but it only
covers *federal* opportunities (relevant here mainly via NEA). Foundation
and corporate giving (Adobe, Disney) and city/county programs (LA County
Arts Commission) require either a paid database (Candid/Foundation
Directory Online, Instrumentl) or manual/web-search tracking — that's what
`search_web.py` is set up for.
