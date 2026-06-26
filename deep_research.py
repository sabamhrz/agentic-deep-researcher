import html
import os
from pathlib import Path

import gradio as gr
from env_config import has_llm_api_key, load_env
from research_manager import ResearchManager

PROJECT_ROOT = Path(__file__).parent
load_env()


def _missing_api_key() -> bool:
    return not has_llm_api_key()

STAGES = [
    ("plan", "Plan", "Map out targeted searches"),
    ("search", "Search", "Gather web sources"),
    ("write", "Write", "Synthesize the report"),
    ("email", "Deliver", "Email the results"),
]

EXAMPLE_TOPICS = [
    "Latest breakthroughs in fusion energy and timeline to commercial viability",
    "How AI agents are changing software development in 2025",
    "Market outlook for electric vehicle battery recycling",
    "Impact of GLP-1 drugs on the healthcare and food industries",
]

CUSTOM_CSS = """
:root {
    --dr-bg: #0b0f1a;
    --dr-surface: rgba(255, 255, 255, 0.04);
    --dr-surface-strong: rgba(255, 255, 255, 0.07);
    --dr-border: rgba(255, 255, 255, 0.1);
    --dr-text: #e8edf7;
    --dr-muted: #94a3b8;
    --dr-accent: #6366f1;
    --dr-accent-soft: rgba(99, 102, 241, 0.15);
    --dr-success: #34d399;
    --dr-glow: rgba(99, 102, 241, 0.35);
}

.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif !important;
}

.dr-hero {
    text-align: center;
    padding: 2.5rem 1.5rem 1.75rem;
    margin-bottom: 1rem;
    border-radius: 16px;
    background:
        radial-gradient(ellipse 80% 60% at 50% -10%, var(--dr-glow), transparent 70%),
        linear-gradient(180deg, var(--dr-surface-strong), transparent);
}

.dr-hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #c7d2fe;
    background: var(--dr-accent-soft);
    margin-bottom: 1rem;
}

.dr-hero h1 {
    margin: 0 0 0.6rem;
    font-size: 2.35rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.15;
    background: linear-gradient(135deg, #f8fafc 0%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.dr-hero p {
    margin: 0 auto;
    max-width: 540px;
    color: var(--dr-muted);
    font-size: 1.02rem;
    line-height: 1.6;
}

.dr-card-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--dr-muted);
    margin: 1.25rem 0 0.65rem;
}

.dr-panel {
    border: 1px solid var(--dr-border);
    border-radius: 14px;
    background: var(--dr-surface);
    padding: 1rem 1.1rem;
    margin-bottom: 0.5rem;
}

.dr-pipeline {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.65rem;
    margin: 0;
}

@media (max-width: 768px) {
    .dr-pipeline { grid-template-columns: repeat(2, 1fr); }
}

.dr-step {
    padding: 0.85rem 0.75rem;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
    text-align: center;
    transition: all 0.25s ease;
}

.dr-step.active {
    background: var(--dr-accent-soft);
}

.dr-step.done {
    background: rgba(52, 211, 153, 0.12);
}

.dr-step.done .dr-step-label {
    color: #bbf7d0;
}

.dr-step-check {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    margin: 0 auto 0.35rem;
    border-radius: 50%;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: #fff;
    font-size: 0.82rem;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(34, 197, 94, 0.35);
}

.dr-step.active .dr-step-check {
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    box-shadow: 0 0 16px var(--dr-glow);
    animation: dr-pulse 1.4s ease-in-out infinite;
}

.dr-pipeline-wrap {
    padding: 0;
}

.dr-progress-wrap {
    margin-top: 0.85rem;
}

.dr-progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: var(--dr-muted);
    margin-bottom: 0.35rem;
}

.dr-progress-track {
    height: 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    overflow: hidden;
}

.dr-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #6366f1, #22c55e);
    transition: width 0.35s ease;
}

.dr-notice {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0;
    border-radius: 0;
    background: transparent;
    font-size: 0.92rem;
    line-height: 1.55;
    color: var(--dr-text);
}

.dr-notice.success {
    color: #d1fae5;
}

.dr-notice.info {
    color: #e0e7ff;
}

.dr-notice.warning {
    color: #fef3c7;
}

.dr-notice-icon {
    font-size: 1.2rem;
    line-height: 1;
    flex-shrink: 0;
}

.dr-panel.dr-notice.success {
    background: rgba(52, 211, 153, 0.1) !important;
}

.dr-panel.dr-notice.info {
    background: rgba(99, 102, 241, 0.1) !important;
}

.dr-panel.dr-notice.warning {
    background: rgba(251, 191, 36, 0.1) !important;
}

.dr-panel.dr-status.error {
    background: rgba(248, 113, 113, 0.08) !important;
}

.dr-step-icon {
    font-size: 1.25rem;
    margin-bottom: 0.25rem;
}

.dr-step-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--dr-text);
}

.dr-step-desc {
    font-size: 0.68rem;
    color: var(--dr-muted);
    margin-top: 0.15rem;
    line-height: 1.3;
}

.dr-status {
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
    padding: 0;
    border-radius: 0;
    background: transparent;
    color: var(--dr-text);
    font-size: 0.92rem;
    line-height: 1.5;
    min-height: 2rem;
}

.dr-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--dr-accent);
    margin-top: 0.45rem;
    flex-shrink: 0;
    animation: dr-pulse 1.4s ease-in-out infinite;
}

.dr-status.done .dr-status-dot {
    background: var(--dr-success);
    animation: none;
}

.dr-notice.empty {
    display: none;
}

.dr-status.error .dr-status-dot {
    background: #f87171;
    animation: none;
}

.dr-config-warning {
    padding: 0.9rem 1rem;
    border-radius: 12px;
    background: rgba(248, 113, 113, 0.1);
    color: #fecaca;
    font-size: 0.92rem;
    line-height: 1.55;
    margin-bottom: 0.75rem;
}

.dr-config-warning code {
    color: #fca5a5;
    background: rgba(0, 0, 0, 0.25);
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
}

@keyframes dr-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.85); }
}

.dr-plan-list {
    margin: 0;
    padding: 0;
    list-style: none;
}

.dr-plan-item {
    padding: 0.7rem 0;
    margin-bottom: 0.45rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.dr-plan-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.dr-plan-query {
    font-weight: 600;
    color: #e2e8f0;
    font-size: 0.88rem;
}

.dr-plan-reason {
    color: var(--dr-muted);
    font-size: 0.8rem;
    margin-top: 0.2rem;
}

.dr-followups {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.dr-followup-chip {
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    font-size: 0.82rem;
    color: #c7d2fe;
    background: var(--dr-accent-soft);
}

.dr-summary {
    font-size: 1rem;
    line-height: 1.7;
    color: #e2e8f0;
}

.dr-trace {
    font-size: 0.8rem;
    color: var(--dr-muted);
    text-align: center;
    padding: 0.5rem;
}

.dr-trace a {
    color: #a5b4fc;
    text-decoration: none;
}

.dr-trace a:hover {
    text-decoration: underline;
}

.dr-empty {
    color: var(--dr-muted);
    font-style: italic;
    font-size: 0.9rem;
}

#run-btn {
    min-height: 48px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    border-radius: 12px !important;
}

#query-input textarea {
    border-radius: 12px !important;
    font-size: 1rem !important;
    line-height: 1.5 !important;
    border: none !important;
    box-shadow: none !important;
}

#report-output {
    border-radius: 0 !important;
    max-height: 70vh;
    overflow-y: auto;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0 !important;
}

.gradio-container .block,
.gradio-container .form,
.gradio-container .gr-group,
.gradio-container .gr-box {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

.gradio-container .dr-panel {
    border: 1px solid var(--dr-border) !important;
    border-radius: 14px !important;
    background: var(--dr-surface) !important;
    padding: 1rem !important;
}

footer { display: none !important; }
"""


def _show_email_success_popup() -> None:
    recipient = os.getenv("RECIPIENT_EMAIL", "").strip()
    if recipient:
        message = f"Your research report was sent to {recipient}. Please check your inbox."
    else:
        message = "Your research report was emailed successfully. Please check your inbox."
    gr.Success(
        message,
        title="Email sent!",
        duration=12,
    )


def _render_pipeline(active_stage: str | None, completed: set[str]) -> str:
    icons = {"plan": "🗺️", "search": "🔍", "write": "✍️", "email": "📧"}
    steps = []
    for key, label, desc in STAGES:
        if key in completed:
            cls = "dr-step done"
            mark = '<div class="dr-step-check">✓</div>'
        elif key == active_stage:
            cls = "dr-step active"
            mark = '<div class="dr-step-check">…</div>'
        else:
            cls = "dr-step"
            mark = f'<div class="dr-step-icon">{icons[key]}</div>'

        steps.append(
            f'<div class="{cls}">'
            f"{mark}"
            f'<div class="dr-step-label">{label}</div>'
            f'<div class="dr-step-desc">{desc}</div>'
            f"</div>"
        )
    return (
        '<div class="dr-pipeline-wrap">'
        '<p class="dr-card-title" style="margin-top:0">Research pipeline</p>'
        f'<div class="dr-pipeline">{"".join(steps)}</div>'
        "</div>"
    )


def _render_progress(completed: int, total: int, visible: bool) -> str:
    if not visible or total <= 0:
        return ""
    percent = int((completed / total) * 100)
    return (
        '<div class="dr-progress-wrap">'
        '<div class="dr-progress-label">'
        f"<span>Search progress</span><span>{completed} of {total}</span>"
        "</div>"
        '<div class="dr-progress-track">'
        f'<div class="dr-progress-fill" style="width:{percent}%;"></div>'
        "</div>"
        "</div>"
    )


def _render_notification(
    message: str = "",
    level: str = "empty",
    title: str = "",
) -> str:
    if not message or level == "empty":
        return '<div class="dr-notice empty"></div>'

    icons = {
        "success": "✅",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
    }
    icon = icons.get(level, "ℹ️")
    heading = f"<strong>{html.escape(title)}</strong><br>" if title else ""
    return (
        f'<div class="dr-panel dr-notice {level}">'
        f'<div class="dr-notice-icon">{icon}</div>'
        f"<div>{heading}{html.escape(message)}</div>"
        f"</div>"
    )


def _render_status(message: str, done: bool = False, error: bool = False) -> str:
  if error:
    cls = "dr-panel dr-status error"
  elif done:
    cls = "dr-panel dr-status done"
  else:
    cls = "dr-panel dr-status"
  return (
    f'<div class="{cls}">'
    f'<div class="dr-status-dot"></div>'
    f"<span>{html.escape(message)}</span>"
    f"</div>"
  )


def _render_config_warning() -> str:
  if not _missing_api_key():
    return ""
  return (
    '<div class="dr-config-warning">'
    "<strong>API key missing.</strong> "
    "Set <code>OPENROUTER_API_KEY</code> or <code>OPENAI_API_KEY</code> in your <code>.env</code> file "
    "and restart the app."
    "</div>"
  )


def _render_plan(searches: list[dict]) -> str:
  if not searches:
    return '<p class="dr-empty">Search plan will appear here…</p>'
  items = []
  for i, s in enumerate(searches, 1):
    items.append(
      f'<li class="dr-plan-item">'
      f'<div class="dr-plan-query">{i}. {html.escape(s["query"])}</div>'
      f'<div class="dr-plan-reason">{html.escape(s["reason"])}</div>'
      f"</li>"
    )
  return f'<ul class="dr-plan-list">{"".join(items)}</ul>'


def _render_follow_ups(questions: list[str]) -> str:
  if not questions:
    return '<p class="dr-empty">Follow-up questions will appear after the report is written.</p>'
  chips = "".join(f'<span class="dr-followup-chip">{html.escape(q)}</span>' for q in questions)
  return f'<div class="dr-followups">{chips}</div>'


def _render_summary(text: str) -> str:
  if not text:
    return '<p class="dr-empty">A concise summary will appear here once research finishes.</p>'
  return f'<div class="dr-summary">{html.escape(text)}</div>'


def _render_trace(url: str) -> str:
  if not url:
    return ""
  return f'<div class="dr-trace">Debug this run on <a href="{url}" target="_blank">OpenAI Traces</a></div>'


def _pack(
    active_stage,
    completed,
    status_message,
    plan_html,
    summary_html,
    report_md,
    follow_ups_html,
    trace_url,
    notification="",
    notification_level="empty",
    notification_title="",
    search_completed=0,
    search_total=0,
    show_search_progress=False,
    status_done=False,
    status_error=False,
):
    pipeline = _render_pipeline(active_stage, completed)
    if show_search_progress:
        pipeline += _render_progress(search_completed, search_total, True)
    return (
        pipeline,
        _render_status(status_message, done=status_done, error=status_error),
        plan_html,
        summary_html,
        report_md,
        follow_ups_html,
        _render_trace(trace_url),
        _render_notification(notification, notification_level, notification_title),
    )


def _initial_state():
    return _pack(
        None,
        set(),
        "Enter a topic and click Start Research to begin.",
        _render_plan([]),
        _render_summary(""),
        "",
        _render_follow_ups([]),
        "",
    )


async def run(query: str):
  if not query or not query.strip():
    yield _pack(
        None, set(), "Please enter a research topic to get started.",
        _render_plan([]), _render_summary(""), "", _render_follow_ups([]), "",
    )
    return

  if _missing_api_key():
    yield _pack(
        None, set(),
        "Missing API key. Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env and restart.",
        _render_plan([]), _render_summary(""), "", _render_follow_ups([]), "",
        status_error=True,
    )
    return

  active_stage: str | None = "plan"
  completed: set[str] = set()
  plan_html = _render_plan([])
  summary_html = _render_summary("")
  report_md = ""
  follow_ups_html = _render_follow_ups([])
  trace_url = ""
  search_completed = 0
  search_total = 0
  show_search_progress = False

  yield _pack(
      active_stage, completed, "Starting research pipeline…",
      plan_html, summary_html, report_md, follow_ups_html, trace_url,
  )

  try:
    async for event in ResearchManager().run(query.strip()):
      kind = event["type"]

      if kind == "trace":
        trace_url = event["url"]

      elif kind == "status":
        active_stage = event["stage"]
        yield _pack(
            active_stage, completed, event["message"],
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
            search_completed=search_completed,
            search_total=search_total,
            show_search_progress=show_search_progress,
        )

      elif kind == "plan":
        plan_html = _render_plan(event["searches"])
        completed.add("plan")
        active_stage = "search"
        yield _pack(
            active_stage, completed,
            f"Plan complete — {len(event['searches'])} searches ready. Gathering sources…",
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
            notification="Search plan created successfully.",
            notification_level="info",
            notification_title="Plan complete",
        )

      elif kind == "search_progress":
        show_search_progress = True
        search_completed = event["completed"]
        search_total = event["total"]
        yield _pack(
            "search", completed,
            f"Searching the web… {search_completed} of {search_total} complete",
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
            search_completed=search_completed,
            search_total=search_total,
            show_search_progress=True,
        )

      elif kind == "search_complete":
        completed.add("search")
        active_stage = "write"
        show_search_progress = False
        yield _pack(
            active_stage, completed,
            f"Search complete — collected {event['count']} result sets. Writing report…",
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
            notification="Web search finished. Synthesizing your report now.",
            notification_level="info",
            notification_title="Search complete",
        )

      elif kind == "summary":
        summary_html = _render_summary(event["text"])

      elif kind == "follow_ups":
        follow_ups_html = _render_follow_ups(event["questions"])

      elif kind == "report":
        report_md = event["markdown"]
        yield _pack(
            "write", completed,
            "Report generated. Preparing email delivery…",
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
        )

      elif kind == "write_complete":
        completed.add("write")
        active_stage = "email"
        yield _pack(
            active_stage, completed,
            "Report ready. Sending email…",
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
            notification="Your report has been written successfully.",
            notification_level="success",
            notification_title="Report complete",
        )

      elif kind == "email":
        completed.add("email")
        active_stage = None
        email_status = event.get("status")
        if email_status == "success":
          _show_email_success_popup()
          yield _pack(
              active_stage, completed,
              "Email sent successfully!",
              plan_html, summary_html, report_md, follow_ups_html, trace_url,
              notification="Your research report was emailed successfully. Check your inbox.",
              notification_level="success",
              notification_title="Email delivered",
              status_done=True,
          )
        elif email_status == "skipped":
          yield _pack(
              active_stage, completed,
              "Report ready. Email skipped (Gmail not configured).",
              plan_html, summary_html, report_md, follow_ups_html, trace_url,
              notification=event.get("message", "Gmail credentials are not configured."),
              notification_level="warning",
              notification_title="Email skipped",
              status_done=True,
          )
        else:
          yield _pack(
              active_stage, completed,
              "Report ready, but email delivery failed.",
              plan_html, summary_html, report_md, follow_ups_html, trace_url,
              notification=event.get("message", "Could not send the email."),
              notification_level="warning",
              notification_title="Email failed",
          )

      elif kind == "complete":
        yield _pack(
            None, completed, event["message"],
            plan_html, summary_html, report_md, follow_ups_html, trace_url,
            notification=event["message"],
            notification_level="success",
            notification_title="All done",
            status_done=True,
        )

  except Exception as exc:
    yield _pack(
        active_stage, completed, f"Research failed: {exc}",
        plan_html, summary_html, report_md, follow_ups_html, trace_url,
        status_error=True,
        notification=str(exc),
        notification_level="error",
        notification_title="Something went wrong",
    )


def _lock_inputs():
  return gr.update(interactive=False), gr.update(interactive=False)


def _unlock_inputs():
  return gr.update(interactive=True), gr.update(interactive=True)


theme = gr.themes.Base(
  primary_hue=gr.themes.colors.indigo,
  secondary_hue=gr.themes.colors.slate,
  neutral_hue=gr.themes.colors.slate,
  font=gr.themes.GoogleFont("Inter"),
).set(
  body_background_fill="*neutral_950",
  body_background_fill_dark="*neutral_950",
  block_background_fill="*neutral_900",
  block_background_fill_dark="*neutral_900",
  block_border_width="0px",
  block_label_text_weight="600",
  input_background_fill="*neutral_800",
  input_background_fill_dark="*neutral_800",
  button_primary_background_fill="linear-gradient(135deg, *primary_500, *primary_600)",
  button_primary_background_fill_hover="linear-gradient(135deg, *primary_400, *primary_500)",
  button_large_padding="12px 24px",
  shadow_drop="0 8px 32px rgba(0,0,0,0.35)",
)

with gr.Blocks(title="Deep Research Agent") as ui:
  gr.HTML(_render_config_warning())
  gr.HTML(
    """
    <div class="dr-hero">
      <div class="dr-hero-badge">✦ AI-powered research assistant</div>
      <h1>Deep Research Agent</h1>
      <p>
        Ask anything. We plan searches, gather sources, write your report,
        and email it — with live progress at every step.
      </p>
    </div>
    """
  )

  notification_html = gr.HTML(_render_notification())

  with gr.Row(equal_height=False):
    with gr.Column(scale=3, elem_classes=["dr-panel"]):
      query_textbox = gr.Textbox(
        label="What would you like to research?",
        placeholder="e.g. What is it like to have an INFJ personality type?",
        lines=3,
        elem_id="query-input",
        show_label=True,
      )
      with gr.Row():
        run_button = gr.Button(
          "Start Research",
          variant="primary",
          scale=2,
          elem_id="run-btn",
        )
        clear_button = gr.Button("Clear", scale=1)

    with gr.Column(scale=2, elem_classes=["dr-panel"]):
      pipeline_html = gr.HTML(_render_pipeline(None, set()))

  status_html = gr.HTML(_render_status("Enter a topic and click Start Research to begin."))

  with gr.Row():
    with gr.Column(elem_classes=["dr-panel"]):
      gr.HTML('<p class="dr-card-title" style="margin-top:0">Search plan</p>')
      plan_html = gr.HTML(_render_plan([]))
    with gr.Column(elem_classes=["dr-panel"]):
      gr.HTML('<p class="dr-card-title" style="margin-top:0">Executive summary</p>')
      summary_html = gr.HTML(_render_summary(""))

  with gr.Column(elem_classes=["dr-panel"]):
    gr.HTML('<p class="dr-card-title" style="margin-top:0">Full report</p>')
    report = gr.Markdown(
      value="",
      elem_id="report-output",
      show_label=False,
    )

  with gr.Column(elem_classes=["dr-panel"]):
    gr.HTML('<p class="dr-card-title" style="margin-top:0">Suggested follow-ups</p>')
    follow_ups_html = gr.HTML(_render_follow_ups([]))

  trace_html = gr.HTML("")

  gr.Examples(
    examples=[[topic] for topic in EXAMPLE_TOPICS],
    inputs=query_textbox,
    label="Try an example",
  )

  outputs = [
    pipeline_html,
    status_html,
    plan_html,
    summary_html,
    report,
    follow_ups_html,
    trace_html,
    notification_html,
  ]

  run_event = run_button.click(_lock_inputs, outputs=[run_button, query_textbox]).then(
    fn=run,
    inputs=query_textbox,
    outputs=outputs,
  ).then(_unlock_inputs, outputs=[run_button, query_textbox])

  query_textbox.submit(_lock_inputs, outputs=[run_button, query_textbox]).then(
    fn=run,
    inputs=query_textbox,
    outputs=outputs,
  ).then(_unlock_inputs, outputs=[run_button, query_textbox])

  clear_button.click(
    fn=_initial_state,
    outputs=outputs,
  ).then(
    fn=lambda: "",
    outputs=query_textbox,
  )

ui.queue()
ui.launch(inbrowser=True, theme=theme, css=CUSTOM_CSS)
