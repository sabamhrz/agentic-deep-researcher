from agents import Agent, ModelSettings, Runner, gen_trace_id, trace
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from write_agent import INSTRUCTIONS as WRITE_INSTRUCTIONS, ReportData
from env_config import (
    EMAIL_TIMEOUT_SECONDS,
    get_run_config,
    get_write_model_candidates,
    load_env,
    using_openrouter,
    WRITE_MAX_TOKENS,
    WRITE_TIMEOUT_SECONDS,
)
from email_delivery import deliver_report_email
from plan_parser import fallback_search_plan, parse_search_plan_json, parse_search_plan_text
from report_parser import fallback_report, parse_report_text
from web_search import search_web_text
import asyncio

load_env()

MAX_PLAN_ATTEMPTS = 3


class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process, yielding structured progress events."""
        trace_id = gen_trace_id()
        trace_url = ""
        if not using_openrouter():
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"

        if using_openrouter():
            async for event in self._run_pipeline(query, trace_url):
                yield event
            return

        with trace("Research trace", trace_id=trace_id):
            async for event in self._run_pipeline(query, trace_url):
                yield event

    async def _run_pipeline(self, query: str, trace_url: str):
        if trace_url:
            print(f"View trace: {trace_url}")
            yield {"type": "trace", "url": trace_url}

        yield {"type": "status", "stage": "plan", "message": "Analyzing your topic and planning search strategy…"}
        search_plan = await self.plan_searches(query)

        yield {
            "type": "plan",
            "searches": [
                {"query": item.query, "reason": item.reason}
                for item in search_plan.searches
            ],
        }

        yield {"type": "status", "stage": "search", "message": "Searching the web in parallel…"}
        search_results = []
        async for event in self.perform_searches(search_plan):
            if event["type"] == "search_progress":
                yield event
            else:
                search_results = event["results"]

        yield {
            "type": "search_complete",
            "count": len(search_results),
        }

        yield {"type": "status", "stage": "write", "message": "Synthesizing findings into a detailed report…"}
        report = await self.write_report(query, search_results)

        yield {"type": "summary", "text": report.short_summary}
        yield {"type": "follow_ups", "questions": report.follow_up_questions}
        yield {"type": "report", "markdown": report.markdown_report}
        yield {"type": "write_complete"}

        yield {"type": "status", "stage": "email", "message": "Sending your report by email…"}
        email_result = await self.send_email(report)
        yield {"type": "email", **email_result}

        complete_message = self._complete_message(email_result)
        yield {"type": "complete", "message": complete_message}

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform for the query."""
        print("Planning searches...")
        last_error: Exception | None = None

        for attempt in range(1, MAX_PLAN_ATTEMPTS + 1):
            try:
                result = await Runner.run(
                    planner_agent,
                    f"Query: {query}",
                    run_config=get_run_config(),
                )
                raw_output = str(result.final_output)
                plan = self._parse_planner_output(raw_output)
                print(f"Will perform {len(plan.searches)} searches")
                return plan
            except Exception as exc:
                last_error = exc
                print(f"Planning attempt {attempt}/{MAX_PLAN_ATTEMPTS} failed: {exc}")

        print(f"Planner failed after {MAX_PLAN_ATTEMPTS} attempts, using fallback plan: {last_error}")
        return fallback_search_plan(query)

    def _parse_planner_output(self, text: str) -> WebSearchPlan:
        parsers = (parse_search_plan_text, parse_search_plan_json)
        errors: list[str] = []

        for parser in parsers:
            try:
                return parser(text)
            except Exception as exc:
                errors.append(f"{parser.__name__}: {exc}")

        raise ValueError("; ".join(errors))

    async def perform_searches(self, search_plan: WebSearchPlan):
        """Perform searches, yielding progress events and final results."""
        print("Searching...")
        num_completed = 0
        total = len(search_plan.searches)
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []

        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{total} completed")
            yield {
                "type": "search_progress",
                "completed": num_completed,
                "total": total,
            }

        print("Finished searching")
        yield {"type": "search_results", "results": results}

    async def search(self, item: WebSearchItem) -> str | None:
        """Fetch web results directly without an extra LLM summarization step."""
        try:
            return await asyncio.to_thread(search_web_text, item.query)
        except Exception as exc:
            print(f"Search failed for '{item.query}': {exc}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the report for the query, trying multiple models before falling back."""
        print("Thinking about report...")
        prompt = self._build_write_prompt(query, search_results)
        last_error: Exception | None = None

        for model in get_write_model_candidates():
            try:
                writer = Agent(
                    name="write_agent",
                    instructions=WRITE_INSTRUCTIONS,
                    model=model,
                    model_settings=ModelSettings(
                        temperature=0.3,
                        max_tokens=WRITE_MAX_TOKENS,
                    ),
                )
                result = await asyncio.wait_for(
                    Runner.run(writer, prompt, run_config=get_run_config()),
                    timeout=WRITE_TIMEOUT_SECONDS,
                )
                report = parse_report_text(str(result.final_output))
                print(f"Finished writing report with model {model}")
                return report
            except Exception as exc:
                last_error = exc
                print(f"Write attempt with {model} failed: {exc}")
                if self._should_skip_to_next_model(exc):
                    continue

        print(f"Writer failed for all models, using fallback report: {last_error}")
        return fallback_report(query, search_results)

    def _build_write_prompt(
        self,
        query: str,
        search_results: list[str],
        max_chars_per_result: int = 1800,
        max_total_chars: int = 9000,
    ) -> str:
        sections: list[str] = []
        total_chars = 0

        for index, result in enumerate(search_results, 1):
            if not result or not result.strip():
                continue

            snippet = result.strip()[:max_chars_per_result]
            remaining = max_total_chars - total_chars
            if remaining <= 0:
                break

            if len(snippet) > remaining:
                snippet = snippet[:remaining]

            sections.append(f"Search {index}:\n{snippet}")
            total_chars += len(snippet)

        research_block = "\n\n".join(sections) if sections else "No search results were collected."
        return f"Original query: {query}\n\nResearch results:\n\n{research_block}"

    @staticmethod
    def _should_skip_to_next_model(exc: Exception) -> bool:
        message = str(exc).lower()
        return any(
            token in message
            for token in ("504", "502", "503", "timeout", "provider returned error", "no choices")
        )

    async def send_email(self, report: ReportData) -> dict:
        print("Sending email...")
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(deliver_report_email, report),
                timeout=EMAIL_TIMEOUT_SECONDS,
            )
            status = result.get("status", "error")
            if status == "success":
                print("Email sent")
            elif status == "skipped":
                print(f"Email skipped: {result.get('message')}")
            else:
                print(f"Email step failed: {result.get('message')}")
            return result
        except Exception as exc:
            print(f"Email step failed: {exc}")
            return {"status": "error", "message": str(exc)}

    @staticmethod
    def _complete_message(email_result: dict) -> str:
        status = email_result.get("status")
        if status == "success":
            return "All done! Your report is ready and has been emailed to you."
        if status == "skipped":
            return "Research complete! Your report is ready. Email was skipped because Gmail is not configured."
        return "Research complete! Your report is ready, but the email could not be sent."
