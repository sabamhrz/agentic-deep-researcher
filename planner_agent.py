from pydantic import BaseModel
from agents import Agent

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."


class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important to the query"

    query: str
    "The search term to use for the web search."

class WebSearchPlan(BaseModel):
    """
    Represents the output of the planning agent, containing the list of targeted web searches to be performed.
    """
    searches: list[WebSearchItem] 

planner_agent = Agent(
    name= "Planner Agent",
    instructions= INSTRUCTIONS,
    model="openai/gpt-oss-120b:free",
    output_type=WebSearchPlan
)