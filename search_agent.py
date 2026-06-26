from agents import Agent, ModelSettings, function_tool

from env_config import get_model_name, load_env
from web_search import search_web_text

load_env()

INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)


@function_tool
def search_web(query: str) -> str:
    """Search the web for a query and return snippets from the top results."""
    return search_web_text(query)


search_agent = Agent(
    name="search_agent",
    model=get_model_name(),
    instructions=INSTRUCTIONS,
    handoff_description="Search the web for a given search term and produce a concise summary of the results.",
    tools=[search_web],
    model_settings=ModelSettings(temperature=0.2, tool_choice="required"),
)
