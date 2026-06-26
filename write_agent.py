from pydantic import BaseModel
from agents import Agent

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

class ReportData(BaseModel):
    short_summary: str
    "A short 2-3 sentence summary of the findings."

    markdown_report: str
    "A detailed markdown report of the findings."

    follow_up_questions: List[str]
    "List of questions that could be asked to further improve the report"

# write_agent - write the final report, 
write_agent = Agent(
    name="write_agent",
    model="openai/gpt-oss-120b:free",
    instructions=INSTRUCTIONS,
    description="Write a cohesive report for a given query and research.",
    output_schema=ReportData
)