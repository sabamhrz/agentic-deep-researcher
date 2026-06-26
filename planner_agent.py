from pydantic import BaseModel
from agents import Agent, ModelSettings

from env_config import get_model_name

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are a research planning assistant.

Given a user query, propose exactly {HOW_MANY_SEARCHES} targeted web searches.

Rules:
- Output ONLY the search blocks below. No introduction, no markdown, no JSON, no commentary.
- Each query must be a short web search phrase (under 12 words).
- Each reason must be one clear sentence.
- Do not number items with "1." — use the SEARCH format exactly.

SEARCH 1
Query: <search phrase>
Reason: <why this search helps answer the topic>

SEARCH 2
Query: <search phrase>
Reason: <why this search helps answer the topic>

Continue until SEARCH {HOW_MANY_SEARCHES}."""


class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important to the query"

    query: str
    "The search term to use for the web search."


class WebSearchPlan(BaseModel):
    """Represents the output of the planning agent."""

    searches: list[WebSearchItem]


planner_agent = Agent(
    name="Planner Agent",
    instructions=INSTRUCTIONS,
    model=get_model_name(),
    model_settings=ModelSettings(temperature=0.2),
)
