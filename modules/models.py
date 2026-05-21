"""
modules/models.py
─────────────────
Pydantic models for lead data validation and enriched lead representation.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class LeadInput(BaseModel):
    """Validates raw form input from the Streamlit UI."""
    full_name: str
    email: EmailStr
    company_name: str
    company_website: Optional[str] = None
    job_title: str
    company_size: Optional[str] = None
    industry: Optional[str] = None
    pain_points: Optional[str] = None
    message: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v

    @field_validator("company_name")
    @classmethod
    def company_not_empty(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters.")
        return v

    @field_validator("company_website", mode="before")
    @classmethod
    def normalize_url(cls, v):
        if not v:
            return v
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class EnrichedLead(BaseModel):
    """Holds all raw + enriched data used for report generation."""
    # Raw form data
    full_name: str
    email: str
    company_name: str
    company_website: Optional[str]
    job_title: str
    company_size: Optional[str]
    industry: Optional[str]
    pain_points: Optional[str]
    message: Optional[str]

    # Enriched data (populated by enrichment module)
    company_description: Optional[str] = None
    company_founded: Optional[str] = None
    company_hq: Optional[str] = None
    key_products_services: Optional[str] = None
    recent_news: Optional[str] = None
    tech_stack: Optional[str] = None
    competitors: Optional[str] = None
    social_links: Optional[str] = None

    # AI-generated insights (populated by Groq)
    executive_summary: Optional[str] = None
    key_challenges: Optional[str] = None
    simplify_value_proposition: Optional[str] = None
    recommended_approach: Optional[str] = None
    talking_points: Optional[str] = None
    personalized_opening: Optional[str] = None

    # Metadata
    submitted_at: str = ""
    report_status: str = "pending"
    pdf_path: Optional[str] = None
    drive_link: Optional[str] = None

    def __init__(self, **data):
        if "submitted_at" not in data or not data["submitted_at"]:
            data["submitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        super().__init__(**data)
