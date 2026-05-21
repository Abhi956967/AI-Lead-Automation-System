"""
modules/google_integration.py
───────────────────────────────
BONUS: Google Drive PDF archival + Google Sheets leads tracker.
Uses a service account — no OAuth browser flow needed.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from modules.models import EnrichedLead

logger = logging.getLogger(__name__)


def _get_drive_service():
    """Build and return a Google Drive API service client."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_path or not Path(sa_path).exists():
        raise FileNotFoundError(f"Service account JSON not found at: {sa_path}")

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    return build("drive", "v3", credentials=creds), creds


def _get_sheets_service(creds):
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=creds)


def upload_to_drive(pdf_path: str, lead: EnrichedLead) -> Optional[str]:
    """
    Upload the PDF report to a Google Drive folder.
    Returns the shareable Drive link or None on failure.
    """
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        logger.warning("GOOGLE_DRIVE_FOLDER_ID not set — skipping Drive upload.")
        return None

    try:
        from googleapiclient.http import MediaFileUpload

        drive_service, _ = _get_drive_service()

        file_metadata = {
            "name": Path(pdf_path).name,
            "parents": [folder_id],
        }
        media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        # Make file viewable by anyone with the link
        drive_service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()

        link = file.get("webViewLink")
        logger.info(f"PDF uploaded to Drive: {link}")
        return link

    except Exception as e:
        logger.error(f"Drive upload failed: {e}")
        return None


def append_to_sheet(lead: EnrichedLead) -> bool:
    """
    Append a new row to the leads Google Sheet.
    Columns: Timestamp | Name | Email | Company | Title | Industry | Status | Drive Link
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        logger.warning("GOOGLE_SHEET_ID not set — skipping Sheets logging.")
        return False

    try:
        _, creds = _get_drive_service()
        sheets_service = _get_sheets_service(creds)

        row = [[
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            lead.full_name,
            lead.email,
            lead.company_name,
            lead.job_title,
            lead.industry or "",
            lead.company_size or "",
            lead.report_status,
            lead.drive_link or "",
        ]]

        sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": row},
        ).execute()

        logger.info(f"Lead logged to Google Sheet: {lead.email}")
        return True

    except Exception as e:
        logger.error(f"Sheets logging failed: {e}")
        return False


def ensure_sheet_headers(sheet_id: str, creds) -> None:
    """Create header row in the sheet if it doesn't exist."""
    try:
        from googleapiclient.discovery import build
        sheets_service = build("sheets", "v4", credentials=creds)

        # Check if header already exists
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range="Sheet1!A1:I1",
        ).execute()

        if not result.get("values"):
            headers = [[
                "Timestamp", "Full Name", "Email", "Company", "Job Title",
                "Industry", "Company Size", "Report Status", "Drive Link"
            ]]
            sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range="Sheet1!A1",
                valueInputOption="USER_ENTERED",
                body={"values": headers},
            ).execute()
            logger.info("Sheet headers created.")
    except Exception as e:
        logger.warning(f"Could not ensure sheet headers: {e}")
