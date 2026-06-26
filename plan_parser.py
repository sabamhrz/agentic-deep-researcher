import re

from planner_agent import HOW_MANY_SEARCHES, WebSearchItem, WebSearchPlan

_SEARCH_BLOCK_RE = re.compile(
    r"SEARCH\s+(\d+)\s*\n\s*Query:\s*(.+?)\n\s*Reason:\s*(.+?)(?=\n\s*SEARCH\s+\d+\s*\n|\Z)",
    re.IGNORECASE | re.DOTALL,
)

_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


def parse_search_plan_text(text: str) -> WebSearchPlan:
    """Parse the planner's plain-text SEARCH blocks into a WebSearchPlan."""
    matches = _SEARCH_BLOCK_RE.findall(text)
    if not matches:
        raise ValueError("No SEARCH blocks found in planner output.")

    searches = [
        WebSearchItem(query=query.strip(), reason=reason.strip())
        for _, query, reason in matches
    ]
    if not searches:
        raise ValueError("Planner returned no usable searches.")

    return WebSearchPlan(searches=searches[:HOW_MANY_SEARCHES])


def parse_search_plan_json(text: str) -> WebSearchPlan:
    """Try to recover a WebSearchPlan from embedded JSON in model output."""
    import json

    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError("No JSON object found in planner output.")

    payload = json.loads(match.group())
    return WebSearchPlan.model_validate(payload)


def fallback_search_plan(query: str) -> WebSearchPlan:
    """Deterministic search plan used when the planner model fails."""
    topic = query.strip()
    templates = [
        (f"{topic} overview", "Establish a broad understanding of the topic."),
        (f"{topic} key facts", "Collect core facts and background information."),
        (f"{topic} recent developments", "Find the latest news and updates."),
        (f"{topic} expert analysis", "Gather expert perspectives and analysis."),
        (f"{topic} challenges and outlook", "Understand limitations and future trends."),
    ]
    searches = [
        WebSearchItem(query=search_query, reason=reason)
        for search_query, reason in templates[:HOW_MANY_SEARCHES]
    ]
    return WebSearchPlan(searches=searches)
