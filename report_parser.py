import re
from typing import List

from write_agent import ReportData

_SUMMARY_RE = re.compile(r"##\s*SUMMARY\s*\n(.*?)(?=\n##\s*FOLLOW_UPS\b|\Z)", re.IGNORECASE | re.DOTALL)
_FOLLOW_UPS_RE = re.compile(r"##\s*FOLLOW_UPS\s*\n(.*?)(?=\n##\s*REPORT\b|\Z)", re.IGNORECASE | re.DOTALL)
_REPORT_RE = re.compile(r"##\s*REPORT\s*\n(.*)\Z", re.IGNORECASE | re.DOTALL)


def parse_report_text(text: str) -> ReportData:
    """Parse the writer agent's sectioned plain-text output."""
    summary_match = _SUMMARY_RE.search(text)
    followups_match = _FOLLOW_UPS_RE.search(text)
    report_match = _REPORT_RE.search(text)

    if not report_match:
        raise ValueError("Missing ## REPORT section in writer output.")

    summary = summary_match.group(1).strip() if summary_match else ""
    follow_up_block = followups_match.group(1).strip() if followups_match else ""
    markdown_report = report_match.group(1).strip()

    follow_up_questions = _parse_follow_ups(follow_up_block)
    if not summary:
        summary = _first_sentences(markdown_report, max_sentences=3)

    return ReportData(
        short_summary=summary,
        markdown_report=markdown_report,
        follow_up_questions=follow_up_questions,
    )


def fallback_report(query: str, search_results: list[str]) -> ReportData:
    """Build a readable report without calling the LLM."""
    usable_results = [result.strip() for result in search_results if result and result.strip()]
    topic = query.strip()

    if not usable_results:
        markdown_report = (
            f"# Research Report: {topic}\n\n"
            "No usable web search results were collected. "
            "Try running the research again with a broader topic."
        )
        return ReportData(
            short_summary=f"No web results were found for '{topic}'.",
            markdown_report=markdown_report,
            follow_up_questions=[f"What are the most recent developments in {topic}?"],
        )

    sections = [f"# Research Report: {topic}\n", "## Collected Findings\n"]
    for index, result in enumerate(usable_results, 1):
        sections.append(f"### Finding {index}\n\n{result}\n")

    sections.append(
        "## Notes\n\nThis report was assembled from raw web search results "
        "because the writing model was unavailable."
    )
    markdown_report = "\n".join(sections)

    return ReportData(
        short_summary=(
            f"Compiled research on '{topic}' from {len(usable_results)} web searches. "
            "Review the findings below for source-backed details."
        ),
        markdown_report=markdown_report,
        follow_up_questions=[
            f"What are the strongest sources on {topic}?",
            f"How has {topic} changed recently?",
            f"What are the main debates around {topic}?",
        ],
    )


def _parse_follow_ups(block: str) -> List[str]:
    if not block:
        return []

    questions = []
    for line in block.splitlines():
        cleaned = re.sub(r"^[\-\*\d\.\)\s]+", "", line).strip()
        if cleaned:
            questions.append(cleaned)
    return questions[:5]


def _first_sentences(text: str, max_sentences: int = 3) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:max_sentences]).strip()
