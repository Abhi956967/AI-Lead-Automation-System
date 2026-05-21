"""
modules/workflow.py
────────────────────
Orchestrates the full end-to-end lead automation pipeline.
Called by the Streamlit UI with a progress callback.
"""

import logging
from typing import Callable, Optional
from modules.models import LeadInput, EnrichedLead
from modules.enrichment import enrich_company
from modules.ai_insights import generate_insights
from modules.pdf_generator import generate_pdf
from modules.email_sender import send_report_email

logger = logging.getLogger(__name__)


def run_pipeline(
    lead_input: LeadInput,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> EnrichedLead:
    """
    Full automation pipeline:
    1. Enrich company data (scraping)
    2. Generate AI insights (Groq)
    3. Generate PDF report
    4. Send email to prospect
    5. (Optional) Upload to Drive + log to Sheets

    progress_callback(pct: float, message: str) — used to update Streamlit UI.
    """

    def update(pct: float, msg: str):
        logger.info(f"[{int(pct*100)}%] {msg}")
        if progress_callback:
            progress_callback(pct, msg)

    update(0.05, "Validating lead information...")

    # Build enriched lead from raw input
    lead = EnrichedLead(
        full_name=lead_input.full_name,
        email=lead_input.email,
        company_name=lead_input.company_name,
        company_website=lead_input.company_website,
        job_title=lead_input.job_title,
        company_size=lead_input.company_size,
        industry=lead_input.industry,
        pain_points=lead_input.pain_points,
        message=lead_input.message,
    )

    # ── Step 1: Web enrichment ────────────────────────────────────
    update(0.15, f"Researching {lead_input.company_name}...")
    try:
        enriched_data = enrich_company(lead_input.company_name, lead_input.company_website)
        for key, value in enriched_data.items():
            if value:
                setattr(lead, key, value)
        update(0.30, "Company data enriched successfully.")
    except Exception as e:
        logger.warning(f"Enrichment partially failed: {e}")
        update(0.30, "Enrichment completed with partial data.")

    # ── Step 2: AI Insights via Groq ─────────────────────────────
    update(0.35, "Generating AI-powered insights with Groq...")
    try:
        lead = generate_insights(lead)
        update(0.60, "Insights generated.")
    except Exception as e:
        logger.error(f"AI insights failed: {e}")
        lead.executive_summary = f"{lead.company_name} is a promising prospect in the {lead.industry or 'business'} sector."
        update(0.60, "Insights generated with fallback content.")

    # ── Step 3: PDF Generation ────────────────────────────────────
    update(0.65, "Building personalized PDF report...")
    try:
        pdf_path = generate_pdf(lead)
        lead.pdf_path = pdf_path
        lead.report_status = "pdf_ready"
        update(0.80, "PDF report created.")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise RuntimeError(f"PDF generation failed: {e}")

    # ── Step 4: Email Delivery ────────────────────────────────────
    update(0.82, f"Sending report to {lead.email}...")
    try:
        send_report_email(lead, pdf_path)
        lead.report_status = "email_sent"
        update(0.90, "Email delivered successfully.")
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        lead.report_status = "email_failed"
        # Don't raise — PDF is still available locally
        update(0.90, f"Email delivery failed: {e}")

    # ── Step 5: Google Drive + Sheets (optional) ──────────────────
    import os
    google_sa = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if google_sa:
        try:
            from modules.google_integration import upload_to_drive, append_to_sheet
            update(0.92, "Uploading to Google Drive...")
            drive_link = upload_to_drive(pdf_path, lead)
            if drive_link:
                lead.drive_link = drive_link

            update(0.96, "Logging to Google Sheets...")
            append_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Google integration failed (non-critical): {e}")

    lead.report_status = "complete"
    update(1.0, "Pipeline complete!")
    return lead
