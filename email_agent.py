import os
import smtplib
from email.mime.text import MIMEText
from typing import Dict

from agents import Agent, function_tool
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

email_model = "openai/gpt-oss-120b:free"


@function_tool
def send_report_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send out an email with the given subject and HTML body."""
    gmail_user = os.environ.get('GMAIL_EMAIL')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('RECIPIENT_EMAIL')

    if not gmail_user or not gmail_password or not recipient:
        return {"status": "error", "message": "Missing GMAIL_EMAIL, GMAIL_APP_PASSWORD, or RECIPIENT_EMAIL"}

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


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="email_agent",
    instructions=INSTRUCTIONS,
    tools=[send_report_email],
    model=email_model,
)