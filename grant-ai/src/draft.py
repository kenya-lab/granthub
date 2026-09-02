"""
Drafts grant application answers by combining:
  - the org knowledge base (config/org_profile.json)
  - the specific opportunity's details (from the database)
  - the exact question being asked

Requires ANTHROPIC_API_KEY in your environment (see .env.example).
"""
import os
import json
from pathlib import Path
import anthropic

from db import get_opportunity, save_draft, init_db

PROFILE_PATH = Path(__file__).resolve().parent.parent / "config" / "org_profile.json"

SYSTEM_PROMPT = """You are a grant writing assistant for a specific organization. \
You will be given the organization's full profile as structured data, details \
about a specific grant opportunity, and a specific question from that grant's \
application. Write a strong, specific, honest draft answer.

Rules:
- Use ONLY facts present in the org profile. Never invent numbers, outcomes, \
  or claims that aren't in the data provided.
- If the profile is missing information needed to answer well (marked \
  "REPLACE ME" or simply absent), do NOT fabricate it. Instead, write the \
  best possible draft around what IS known, and separately list exactly what \
  info is missing so the user can fill it in.
- Match the tone to a grant application: clear, concrete, outcome-focused, \
  no fluff.
- If the question has a word or character limit, respect it.
- Output ONLY valid JSON with this shape, nothing else:
  {"draft_answer": "...", "gaps_flagged": "..." or null}
"""


def load_profile():
    with open(PROFILE_PATH) as f:
        return json.load(f)


def draft_answer(opportunity_id: str, question: str, word_limit: int = None):
    profile = load_profile()
    opp = get_opportunity(opportunity_id)
    if opp is None:
        raise ValueError(f"No opportunity found with id {opportunity_id}. "
                          f"Run a search first or add it manually.")

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    user_content = f"""ORG PROFILE:
{json.dumps(profile, indent=2)}

GRANT OPPORTUNITY:
Title: {opp.get('title')}
Funder: {opp.get('funder')}
Eligibility: {opp.get('eligibility')}
Deadline: {opp.get('deadline')}
Description: {opp.get('description')}

QUESTION TO ANSWER:
{question}

WORD LIMIT: {word_limit if word_limit else 'none specified'}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    parsed = json.loads(text)

    save_draft(
        opportunity_id=opportunity_id,
        question=question,
        draft_answer=parsed.get("draft_answer"),
        word_limit=word_limit,
        gaps_flagged=parsed.get("gaps_flagged"),
    )
    return parsed


if __name__ == "__main__":
    init_db()
    import sys
    if len(sys.argv) < 3:
        print("Usage: python draft.py <opportunity_id> \"<question>\" [word_limit]")
        sys.exit(1)
    opp_id = sys.argv[1]
    question = sys.argv[2]
    wl = int(sys.argv[3]) if len(sys.argv) > 3 else None
    result = draft_answer(opp_id, question, wl)
    print("\n--- DRAFT ---\n")
    print(result["draft_answer"])
    if result.get("gaps_flagged"):
        print("\n--- INFO NEEDED FROM YOU ---\n")
        print(result["gaps_flagged"])
