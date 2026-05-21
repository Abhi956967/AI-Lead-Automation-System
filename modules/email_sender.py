"""
modules/email_sender.py
────────────────────────
Sends the personalized audit report PDF to the prospect via email.
Supports Gmail SMTP and SendGrid.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from modules.models import EnrichedLead

logger = logging.getLogger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 12px;
                  overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
    .header {{ background: #1d4ed8; padding: 32px 40px; }}
    .header h1 {{ color: white; margin: 0; font-size: 22px; font-weight: 700; }}
    .header p  {{ color: #bfdbfe; margin: 6px 0 0; font-size: 13px; }}
    .body {{ padding: 36px 40px; }}
    .greeting {{ font-size: 16px; color: #0f172a; font-weight: 600; margin-bottom: 16px; }}
    .text {{ font-size: 14px; color: #374151; line-height: 1.7; margin-bottom: 16px; }}
    .highlight {{ background: #eff6ff; border-left: 4px solid #1d4ed8; padding: 14px 18px;
                  border-radius: 6px; font-size: 13px; color: #1e40af; margin: 20px 0; font-style: italic; }}
    .button {{ display: inline-block; background: #1d4ed8; color: white !important;
               padding: 12px 28px; border-radius: 8px; text-decoration: none;
               font-weight: 600; font-size: 14px; margin: 16px 0; }}
    .footer {{ background: #f1f5f9; padding: 20px 40px; font-size: 12px; color: #94a3b8; }}
    .company {{ font-size: 13px; color: #64748b; margin-top: 8px; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>SimplifIQ &mdash; Your Business Intelligence Report</h1>
      <p>Prepared exclusively for {full_name} &bull; {company_name}</p>
    </div>
    <div class="body">
      <p class="greeting">Hi {first_name},</p>
      <p class="text">{personalized_opening}</p>
      <p class="text">
        We've prepared a detailed AI Opportunity &amp; Automation Audit for <strong>{company_name}</strong>.
        Inside, you'll find:
      </p>
      <ul class="text">
        <li>A company overview and market context</li>
        <li>The top business challenges we identified for your industry and size</li>
        <li>Specific AI automation workflows we recommend for {company_name}</li>
        <li>Personalized talking points for our discovery conversation</li>
        <li>Clear next steps to get started</li>
      </ul>
      <div class="highlight">
        {executive_summary}
      </div>
      <p class="text">
        The full report is attached to this email as a PDF. We'd love to walk you through it
        on a 30-minute call at your convenience.
      </p>
      <hr>
      <p class="text" style="font-size:13px; color:#64748b;">
        This report was generated specifically for {company_name} by SimplifIQ's
        AI intelligence platform. If you have any questions before our call, reply
        to this email and our team will get back to you within one business day.
      </p>
    </div>
    <div class="footer">
      SimplifIQ &bull; AI-Powered Business Automation &bull; hello@simplifyiq.ai<br>
      &copy; {year} SimplifIQ. All rights reserved. This report is confidential.
    </div>
  </div>
</body>
</html>
"""


def build_email_body(lead: EnrichedLead) -> tuple[str, str]:
    """Returns (plain_text, html) email body."""
    from datetime import datetime
    first_name = lead.full_name.split()[0]
    opening = lead.personalized_opening or f"Thank you for your interest in SimplifIQ."
    summary = lead.executive_summary or f"We've completed our analysis of {lead.company_name}."

    plain = (
        f"Hi {first_name},\n\n"
        f"{opening}\n\n"
        f"We've attached a personalized AI Opportunity & Automation Audit for {lead.company_name}.\n\n"
        f"Summary: {summary}\n\n"
        f"Please review the attached PDF report. We'd love to schedule a 30-minute discovery call.\n\n"
        f"Best regards,\nSimplIQ Intelligence Team\nhello@simplifyiq.ai"
    )

    html = HTML_TEMPLATE.format(
        full_name=lead.full_name,
        first_name=first_name,
        company_name=lead.company_name,
        personalized_opening=opening,
        executive_summary=summary,
        year=datetime.now().year,
    )
    return plain, html


def send_via_smtp(lead: EnrichedLead, pdf_path: str) -> bool:
    """Send email via Gmail SMTP (or any SMTP server)."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        raise ValueError("SMTP_EMAIL and SMTP_PASSWORD must be set in environment.")

    plain, html = build_email_body(lead)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your SimplifIQ Report: {lead.company_name} AI Opportunity Audit"
    msg["From"] = f"SimplifIQ Intelligence <{sender_email}>"
    msg["To"] = lead.email
    msg["Reply-To"] = sender_email

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Attach PDF
    if pdf_path and Path(pdf_path).exists():
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = Path(pdf_path).name
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, lead.email, msg.as_string())

    logger.info(f"Email sent via SMTP to {lead.email}")
    return True


def send_via_sendgrid(lead: EnrichedLead, pdf_path: str) -> bool:
    """Send email via SendGrid API."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import (
            Mail, Attachment, FileContent, FileName, FileType, Disposition
        )
        import base64

        api_key = os.getenv("SENDGRID_API_KEY")
        sender = os.getenv("SENDER_EMAIL")
        if not api_key or not sender:
            raise ValueError("SENDGRID_API_KEY and SENDER_EMAIL must be set.")

        plain, html = build_email_body(lead)

        message = Mail(
            from_email=sender,
            to_emails=lead.email,
            subject=f"Your SimplifIQ Report: {lead.company_name} AI Opportunity Audit",
            plain_text_content=plain,
            html_content=html,
        )

        if pdf_path and Path(pdf_path).exists():
            with open(pdf_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            attachment = Attachment(
                FileContent(data),
                FileName(Path(pdf_path).name),
                FileType("application/pdf"),
                Disposition("attachment"),
            )
            message.attachment = attachment

        sg = SendGridAPIClient(api_key)
        sg.send(message)
        logger.info(f"Email sent via SendGrid to {lead.email}")
        return True
    except ImportError:
        logger.error("sendgrid package not installed.")
        return False


def send_report_email(lead: EnrichedLead, pdf_path: str) -> bool:
    """Main entry point — auto-selects email method from env."""
    method = os.getenv("EMAIL_METHOD", "smtp").lower()
    try:
        if method == "sendgrid":
            return send_via_sendgrid(lead, pdf_path)
        else:
            return send_via_smtp(lead, pdf_path)
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        raise
