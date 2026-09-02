"""
Command-line entry point.

  python cli.py init                          - set up the database
  python cli.py search-federal                 - pull grants.gov matches
  python cli.py list [status]                   - list indexed opportunities
  python cli.py show <opportunity_id>            - show one opportunity in full
  python cli.py status <opportunity_id> <status> - update status
  python cli.py draft <opportunity_id> "<question>" [word_limit]
"""
import sys
import json

from db import init_db, list_opportunities, get_opportunity, update_status
from search_grants_gov import search_grants_gov
from draft import draft_answer


def cmd_list(status=None):
    opps = list_opportunities(status=status)
    if not opps:
        print("No opportunities indexed yet. Run 'search-federal' first.")
        return
    for o in opps:
        print(f"[{o['status']:10}] {o['id']:25} {o['deadline'] or 'no deadline':12} "
              f"{o['funder'] or '':30} {o['title']}")


def cmd_show(opp_id):
    o = get_opportunity(opp_id)
    if not o:
        print(f"No opportunity found with id {opp_id}")
        return
    print(json.dumps(o, indent=2))


def main():
    init_db()
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "init":
        print("Database initialized.")
    elif cmd == "search-federal":
        queries = ["arts education youth", "summer camp enrichment", "arts nonprofit community"]
        total = 0
        for q in queries:
            found = search_grants_gov(q)
            print(f"'{q}': {len(found)} results")
            total += len(found)
        print(f"Indexed {total} results from grants.gov.")
    elif cmd == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_list(status)
    elif cmd == "show":
        cmd_show(sys.argv[2])
    elif cmd == "status":
        update_status(sys.argv[2], sys.argv[3])
        print(f"Updated {sys.argv[2]} to status '{sys.argv[3]}'")
    elif cmd == "draft":
        opp_id = sys.argv[2]
        question = sys.argv[3]
        wl = int(sys.argv[4]) if len(sys.argv) > 4 else None
        result = draft_answer(opp_id, question, wl)
        print("\n--- DRAFT ---\n")
        print(result["draft_answer"])
        if result.get("gaps_flagged"):
            print("\n--- INFO NEEDED FROM YOU ---\n")
            print(result["gaps_flagged"])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
