from typing import List

from pydantic import BaseModel
from agents import Agent, ModelSettings

from env_config import WRITE_MAX_TOKENS, get_model_name

INSTRUCTIONS = """You are a senior researcher writing a detailed markdown report.

You will receive the original query and summarized search results.

Output ONLY these three sections, in this exact order:

## SUMMARY
Write 2-3 sentences summarizing the key findings.

## FOLLOW_UPS
List 3-5 follow-up questions as bullet points using "- ".

## REPORT
Write a clear markdown report with headings. Aim for 400-600 words.
Use only the provided research. Do not add JSON or extra sections."""


class ReportData(BaseModel):
    short_summary: str
    "A short 2-3 sentence summary of the findings."

    markdown_report: str
    "A detailed markdown report of the findings."

    follow_up_questions: List[str]
    "List of questions that could be asked to further improve the report"


def build_write_agent(model: str | None = None) -> Agent:
    """Build a write agent, optionally overriding the model for fallback retries."""
    return Agent(
        name="write_agent",
        instructions=INSTRUCTIONS,
        model=model or get_model_name(),
        handoff_description="Write a cohesive report for a given query and research.",
        model_settings=ModelSettings(temperature=0.3, max_tokens=WRITE_MAX_TOKENS),
    )


write_agent = build_write_agent()
