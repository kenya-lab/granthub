"""
Several funder categories don't expose public search APIs the way grants.gov
does: named foundations/corporate giving (Adobe, Disney), CDFIs, LA City
Council district discretionary funds, and LA County Board of Supervisors
district funds. The intended workflow is:

  1. Open this project in Claude Code.
  2. Ask Claude Code (which has a real web_search tool) to work through
     config/search_sources.json — it lists each category, why it matters,
     and example queries to run. For CDFIs specifically, tell it to only
     log genuine GRANT or technical-assistance programs, not loan products.
     For council districts, make sure config/org_profile.json's "location"
     section is filled in first so it searches the right district.
  3. Have it call add_manual_opportunity() below for each real result so it
     lands in the same database and dashboard as the grants.gov results.

This keeps "search the live web" as something Claude Code does interactively
(where it's fast, current, and can read full pages) rather than something
this script tries to do blind. Re-run this on a schedule (e.g. monthly,
since these categories mostly have annual or rolling cycles rather than the
constant churn of grants.gov) by asking Claude Code to repeat step 2.
"""
from db import upsert_opportunity, init_db


def add_manual_opportunity(
    opp_id: str,
    title: str,
    funder: str,
    deadline: str = None,
    amount_floor: float = None,
    amount_ceiling: float = None,
    eligibility: str = None,
    description: str = None,
    url: str = None,
    org_project: str = "Innervision Arts Academy",
    funder_category: str = None,
):
    """Add or update an opportunity found via manual/live web search.

    funder_category: one of 'CDFI', 'foundation', 'council_district',
    'corporate', 'county', or similar — used to filter/report by category
    later (e.g. to double check no CDFI loan products slipped in as grants).
    """
    opp = {
        "id": opp_id,
        "source": "web",
        "title": title,
        "funder": funder,
        "deadline": deadline,
        "amount_floor": amount_floor,
        "amount_ceiling": amount_ceiling,
        "eligibility": eligibility,
        "description": description,
        "url": url,
        "org_project": org_project,
        "funder_category": funder_category,
        "status": "new",
    }
    upsert_opportunity(opp)
    return opp


if __name__ == "__main__":
    init_db()
    # Example — replace with real results once you run the search in Claude Code.
    add_manual_opportunity(
        opp_id="manual-example-1",
        title="EXAMPLE: LA County Arts Commission — Organizational Grant",
        funder="LA County Arts Commission",
        deadline=None,
        description="Placeholder row — replace by running a live web search in Claude Code.",
    )
    print("Added example placeholder row. Replace with real search results.")
