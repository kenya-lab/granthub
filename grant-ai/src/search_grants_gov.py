"""
Pulls opportunities from the grants.gov public Search2 API and indexes them.
No API key required. Docs: https://www.grants.gov/api/search2

This covers FEDERAL grants (e.g. NEA). It will NOT surface things like the
LA County Arts Commission or Adobe/Disney corporate giving — those don't have
public search APIs, so use search_web.py (run inside Claude Code, which has
live web search) for those on a regular cadence instead.
"""
import requests
from datetime import datetime
from db import upsert_opportunity, init_db

SEARCH_URL = "https://api.grants.gov/v1/api/search2"


def search_grants_gov(keyword: str, rows: int = 25, eligibilities: list = None):
    """
    keyword: free text query, e.g. "arts education youth"
    eligibilities: grants.gov eligibility codes, e.g. ["12"] for "Others" /
                   "25" for nonprofits without 501(c)(3) — check grants.gov docs
                   for the current code list if you want to filter tightly.
    """
    payload = {
        "keyword": keyword,
        "rows": rows,
        "oppStatuses": "posted",  # only currently open opportunities
    }
    if eligibilities:
        payload["eligibilities"] = ",".join(eligibilities)

    resp = requests.post(SEARCH_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    hits = data.get("data", {}).get("oppHits", [])
    results = []
    for hit in hits:
        opp = {
            "id": f"grantsgov-{hit.get('id')}",
            "source": "grants.gov",
            "title": hit.get("title"),
            "funder": hit.get("agencyName", "Federal (grants.gov)"),
            "description": None,  # summary requires a follow-up detail call
            "eligibility": hit.get("eligibleApplicants"),
            "deadline": hit.get("closeDate"),
            "url": f"https://www.grants.gov/search-results-detail/{hit.get('id')}",
            "raw_json": hit,
            "status": "new",
        }
        results.append(opp)
        upsert_opportunity(opp)

    return results


if __name__ == "__main__":
    init_db()
    # Example run for Innervision Arts Academy — adjust keywords to taste.
    queries = [
        "arts education youth",
        "summer camp enrichment",
        "arts nonprofit community",
    ]
    total = 0
    for q in queries:
        found = search_grants_gov(q)
        print(f"'{q}': {len(found)} results indexed")
        total += len(found)
    print(f"Done. {total} opportunities indexed (duplicates merged automatically).")
    print(f"Run at {datetime.now().isoformat()}")
