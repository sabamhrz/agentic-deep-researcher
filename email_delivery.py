import html
import os
import re
import smtplib
from email.mime.text import MIMEText
from typing import Dict

from write_agent import ReportData


def deliver_report_email(report: ReportData) -> Dict[str, str]:
    """Send the report as HTML email without using an LLM."""
    gmail_user = os.environ.get("GMAIL_EMAIL")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not gmail_user or not gmail_password or not recipient:
        return {
            "status": "skipped",
            "message": "Missing GMAIL_EMAIL, GMAIL_APP_PASSWORD, or RECIPIENT_EMAIL",
        }

    subject = _build_subject(report.short_summary)
    html_body = _build_html_email(report)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        server.login(gmail_user, gmail_password)

        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = recipient

        server.sendmail(gmail_user, recipient, msg.as_string())
        server.quit()
        return {"status": "success"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _build_subject(summary: str) -> str:
    cleaned = re.sub(r"\s+", " ", summary).strip()
    if not cleaned:
        return "Deep Research Report"
    if len(cleaned) > 90:
        cleaned = cleaned[:87].rstrip() + "..."
    return f"Deep Research: {cleaned}"


def _build_html_email(report: ReportData) -> str:
    summary = html.escape(report.short_summary)
    body = _markdown_to_html(report.markdown_report)
    follow_ups = "".join(
        f"<li>{html.escape(question)}</li>"
        for question in report.follow_up_questions
    )

    follow_up_block = ""
    if follow_ups:
        follow_up_block = f"""
        <h2 style="color:#4338ca;margin-top:28px;">Suggested follow-ups</h2>
        <ul style="padding-left:20px;">{follow_ups}</ul>
        """

    return f"""<!DOCTYPE html>
<html>
  <body style="font-family:Segoe UI,Arial,sans-serif;line-height:1.6;color:#1f2937;max-width:820px;margin:0 auto;padding:24px;">
    <div style="border-bottom:3px solid #6366f1;padding-bottom:12px;margin-bottom:20px;">
      <h1 style="margin:0;color:#312e81;font-size:24px;">Deep Research Report</h1>
    </div>
    <h2 style="color:#4338ca;">Executive Summary</h2>
    <p>{summary}</p>
    <h2 style="color:#4338ca;margin-top:28px;">Full Report</h2>
    {body}
    {follow_up_block}
  </body>
</html>"""


def _markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    parts: list[str] = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("### "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith("- "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{html.escape(stripped[2:])}</li>")
        elif stripped:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{html.escape(stripped)}</p>")
        elif in_list:
            parts.append("</ul>")
            in_list = False

    if in_list:
        parts.append("</ul>")

    return "\n".join(parts) if parts else f"<p>{html.escape(markdown_text)}</p>"
