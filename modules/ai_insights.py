"""
modules/ai_insights.py
───────────────────────
Uses Groq API (llama-3.3-70b-versatile) to generate personalized
audit insights based on enriched company data.
"""

import os
import logging
from groq import Groq
from modules.models import EnrichedLead

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables.")
    return Groq(api_key=api_key)


def build_context(lead: EnrichedLead) -> str:
    """Build a rich context string from all enriched data."""
    return f"""
LEAD INFORMATION:
- Name: {lead.full_name}
- Title: {lead.job_title}
- Email: {lead.email}
- Company: {lead.company_name}
- Website: {lead.company_website or 'Unknown'}
- Industry: {lead.industry or 'Unknown'}
- Company Size: {lead.company_size or 'Unknown'}
- Pain Points Mentioned: {lead.pain_points or 'Not specified'}
- Their Message: {lead.message or 'None'}

ENRICHED COMPANY DATA:
- Description: {lead.company_description or 'Unavailable'}
- Founded: {lead.company_founded or 'Unknown'}
- HQ: {lead.company_hq or 'Unknown'}
- Key Products/Services: {lead.key_products_services or 'Not identified'}
- Tech Stack Detected: {lead.tech_stack or 'Unknown'}
- Recent News: {lead.recent_news or 'None found'}
- Social Presence: {lead.social_links or 'Not found'}
""".strip()


def call_groq(client: Groq, system: str, user: str) -> str:
    """Make a single Groq API call and return the text response."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return "Unable to generate this section due to an API error."


def generate_insights(lead: EnrichedLead) -> EnrichedLead:
    """
    Calls Groq multiple times to generate each section of the report.
    Returns the same lead object with AI fields populated.
    """
    client = get_groq_client()
    context = build_context(lead)

    system_base = (
        "You are a senior B2B sales strategist and business analyst at SimplifIQ, "
        "an AI-powered automation company. You produce precise, professional, and "
        "highly personalized business intelligence reports. Write in a confident but "
        "consultative tone. Be specific — reference actual company details. Never be generic."
    )

    # 1. Executive Summary
    lead.executive_summary = call_groq(
        client, system_base,
        f"{context}\n\nWrite a 3-4 sentence executive summary of this company from the perspective "
        f"of a consultant doing a first audit. Be specific about what they do, who they serve, "
        f"and their market position."
    )

    # 2. Key Challenges
    lead.key_challenges = call_groq(
        client, system_base,
        f"{context}\n\nIdentify 3 specific operational or growth challenges this company is likely facing "
        f"based on their industry, size, and the pain points mentioned. "
        f"Format as a numbered list with 1-2 sentences per challenge."
    )

    # 3. SimplifIQ Value Proposition (personalized)
    lead.simplify_value_proposition = call_groq(
        client, system_base,
        f"{context}\n\nWrite a personalized value proposition explaining how SimplifIQ's AI automation "
        f"solutions can specifically help {lead.company_name} address their challenges. "
        f"Reference their specific pain points and company context. 2-3 sentences."
    )

    # 4. Recommended Approach
    lead.recommended_approach = call_groq(
        client, system_base,
        f"{context}\n\nRecommend 3 specific AI automation workflows or solutions that would benefit "
        f"{lead.company_name} most. For each, give a title and 1-2 sentences on impact. "
        f"Format: numbered list."
    )

    # 5. Talking Points for Sales Call
    lead.talking_points = call_groq(
        client, system_base,
        f"{context}\n\nCreate 4 sharp, specific talking points for a first sales call with {lead.full_name} "
        f"at {lead.company_name}. Each should open a conversation about a real business need. "
        f"Format as bullet points starting with a bold hook phrase."
    )

    # 6. Personalized Opening for Email
    lead.personalized_opening = call_groq(
        client, system_base,
        f"{context}\n\nWrite a 2-3 sentence personalized email opening paragraph to {lead.full_name} "
        f"that references something specific about {lead.company_name} to show you've done your research. "
        f"It should feel human, warm, and intelligent — not salesy."
    )

    lead.report_status = "insights_ready"
    return lead
