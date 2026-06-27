import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict

from agents import Agent, ModelSettings, function_tool
from env_config import get_model_name, load_env

load_env()


@function_tool
def send_report_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send out an email with the given subject and HTML body."""
    gmail_user = os.environ.get('GMAIL_EMAIL')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not gmail_user or not gmail_password or not recipient:
        return {
            "status": "skipped",
            "message": "Missing GMAIL_EMAIL, GMAIL_APP_PASSWORD, or RECIPIENT_EMAIL",
        }

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)

        msg = MIMEText(html_body, 'html')
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = recipient

        server.sendmail(gmail_user, recipient, msg.as_string())
        server.quit()
        return {"status": "success"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed research report.
You will receive the executive summary, full markdown report, and follow-up questions.
Use your send_report_email tool exactly once to deliver the report as clean HTML with an appropriate subject line.
Convert markdown headings and bullet lists into HTML. Do not send more than one email."""

email_agent = Agent(
    name="email_agent",
    instructions=INSTRUCTIONS,
    tools=[send_report_email],
    model=get_model_name(),
    model_settings=ModelSettings(temperature=0.2, tool_choice="required"),
)