"""
modules/pdf_generator.py
------------------------
Generates a visually professional, personalized PDF audit report using FPDF2.
No external fonts required.
"""

import logging
import os
import unicodedata
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from modules.models import EnrichedLead

logger = logging.getLogger(__name__)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
DARK_NAVY = (15, 23, 42)
ACCENT_BLUE = (37, 99, 235)
LIGHT_BLUE = (219, 234, 254)
MID_GRAY = (100, 116, 139)
LIGHT_GRAY = (241, 245, 249)
WHITE = (255, 255, 255)
DIVIDER = (203, 213, 225)
SUCCESS_GRN = (22, 163, 74)


def pdf_text(value: object, fallback: str = "") -> str:
    """Return text that can be rendered with FPDF core fonts."""
    if value is None:
        return fallback

    text = str(value)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\u00a0": " ",
        "\u2122": "(TM)",
        "\u00ae": "(R)",
        "\u00a9": "(C)",
    }
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)

    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")


def has_value(value: object) -> bool:
    text = pdf_text(value).strip()
    return bool(text) and text.lower() not in {"unknown", "none", "not found", "not specified"}


class LeadReportPDF(FPDF):
    def __init__(self, lead: EnrichedLead):
        super().__init__()
        self.lead = lead
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_fill_color(*ACCENT_BLUE)
        self.rect(0, 0, 210, 4, style="F")

        if self.page_no() > 1:
            self.set_y(8)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*ACCENT_BLUE)
            self.cell(0, 6, "SimplifIQ  |  AI Automation Intelligence", align="L")
            self.set_text_color(*MID_GRAY)
            self.set_font("Helvetica", "", 8)
            self.cell(
                0,
                6,
                f"Confidential Report  |  {pdf_text(self.lead.company_name)}",
                align="R",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.set_draw_color(*DIVIDER)
            self.set_line_width(0.3)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*DIVIDER)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MID_GRAY)
        self.cell(
            0,
            5,
            f"Page {self.page_no()} | Generated {datetime.now().strftime('%B %d, %Y')} | SimplifIQ Confidential",
            align="C",
        )

    def section_heading(self, title: str):
        self.ln(4)
        y = self.get_y()
        self.set_fill_color(*ACCENT_BLUE)
        self.rect(20, y, 3, 7, style="F")
        self.set_xy(25, y)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*DARK_NAVY)
        self.cell(0, 7, f"  {pdf_text(title)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*DIVIDER)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(3)

    def body_text(self, text: object, indent: int = 0):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_NAVY)
        self.set_x(20 + indent)
        self.multi_cell(170 - indent, 5.5, pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def info_chip(self, label: str, value: object):
        if not has_value(value):
            return

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*ACCENT_BLUE)
        self.cell(40, 6, f"{pdf_text(label)}:", new_x=XPos.RIGHT)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK_NAVY)
        self.multi_cell(130, 6, pdf_text(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def highlight_box(self, text: object, color=None):
        self.set_fill_color(*(color or LIGHT_BLUE))
        self.set_draw_color(*ACCENT_BLUE)
        self.set_line_width(0.3)
        self.set_font("Helvetica", "I", 9.5)
        self.set_text_color(30, 60, 120)
        self.set_x(20)
        self.multi_cell(
            170,
            5.5,
            pdf_text(text),
            border=1,
            fill=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(3)

    def list_lines(self, text: object, accent_color=ACCENT_BLUE):
        for raw_line in pdf_text(text).splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line[0].isdigit():
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(*accent_color)
                self.set_x(20)
                self.multi_cell(170, 5.5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                self.set_font("Helvetica", "", 10)
                self.set_text_color(*DARK_NAVY)
                self.set_x(25)
                self.multi_cell(165, 5.5, line.lstrip("-* "), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)


def generate_pdf(lead: EnrichedLead) -> str:
    """Generate the PDF report and return its file path."""
    pdf = LeadReportPDF(lead)
    pdf.add_page()

    # Cover page
    pdf.set_y(30)

    pdf.set_fill_color(*ACCENT_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(
        0,
        8,
        "  CONFIDENTIAL BUSINESS INTELLIGENCE REPORT  ",
        align="C",
        fill=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.ln(12)

    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*DARK_NAVY)
    pdf.multi_cell(0, 14, pdf_text(lead.company_name), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 8, "AI Opportunity & Automation Audit", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)
    pdf.set_draw_color(*ACCENT_BLUE)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)

    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_draw_color(*DIVIDER)
    pdf.set_line_width(0.3)
    pdf.set_x(40)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(130, 7, "Prepared exclusively for", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(40)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*DARK_NAVY)
    pdf.cell(130, 9, pdf_text(lead.full_name), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(40)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(130, 6, pdf_text(lead.job_title), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(40)
    pdf.cell(130, 6, pdf_text(lead.email), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(20)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MID_GRAY)
    pdf.cell(0, 5, "Prepared by  SimplifIQ Intelligence Team", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, datetime.now().strftime("Report Date: %B %d, %Y"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Company overview and executive summary
    pdf.add_page()

    if has_value(lead.personalized_opening):
        pdf.highlight_box(f'"{pdf_text(lead.personalized_opening)}"')

    pdf.section_heading("Company Overview")
    pdf.info_chip("Industry", lead.industry)
    pdf.info_chip("Company Size", lead.company_size)
    pdf.info_chip("Website", lead.company_website)
    pdf.info_chip("Founded", lead.company_founded)
    pdf.info_chip("Headquarters", lead.company_hq)
    pdf.info_chip("Tech Stack", lead.tech_stack)
    pdf.info_chip("Social Links", lead.social_links)
    pdf.ln(2)

    if has_value(lead.company_description):
        pdf.section_heading("Company Description")
        pdf.body_text(lead.company_description)

    if has_value(lead.executive_summary):
        pdf.section_heading("Executive Summary")
        pdf.body_text(lead.executive_summary)

    # Insights and challenges
    pdf.add_page()

    if has_value(lead.recent_news):
        pdf.section_heading("Recent News & Market Activity")
        pdf.body_text(lead.recent_news)

    if has_value(lead.key_challenges):
        pdf.section_heading("Key Business Challenges Identified")
        pdf.list_lines(lead.key_challenges, accent_color=ACCENT_BLUE)

    # SimplifIQ recommendations
    pdf.add_page()

    if has_value(lead.simplify_value_proposition):
        pdf.section_heading("How SimplifIQ Can Help")
        pdf.highlight_box(lead.simplify_value_proposition, color=(220, 252, 231))

    if has_value(lead.recommended_approach):
        pdf.section_heading("Recommended Automation Workflows")
        pdf.list_lines(lead.recommended_approach, accent_color=SUCCESS_GRN)

    if has_value(lead.talking_points):
        pdf.section_heading("Sales Call Talking Points")
        for raw_line in pdf_text(lead.talking_points).splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith(("-", "*")):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*DARK_NAVY)
                pdf.set_x(22)
                pdf.multi_cell(168, 5.5, "  " + line.lstrip("-* "), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                pdf.set_font("Helvetica", "", 9.5)
                pdf.set_text_color(*MID_GRAY)
                pdf.set_x(27)
                pdf.multi_cell(163, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

    # Next steps
    pdf.add_page()
    pdf.section_heading("Recommended Next Steps")

    steps = [
        (
            "Schedule a Discovery Call",
            "Book a 30-minute call with our solutions team to discuss your specific automation goals.",
        ),
        (
            "Review Our Automation Playbook",
            "We'll share case studies from similar companies in your industry with measurable ROI.",
        ),
        (
            "Proof of Concept",
            "We offer a no-cost 2-week pilot to demonstrate the impact of our AI workflows in your environment.",
        ),
        (
            "ROI Projection",
            "Our team will prepare a custom ROI model based on your team size and current workflows.",
        ),
    ]

    for i, (title, desc) in enumerate(steps, 1):
        pdf.set_fill_color(*ACCENT_BLUE)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(7, 7, str(i), align="C", fill=True)
        pdf.set_x(pdf.get_x() + 3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_NAVY)
        pdf.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(30)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*MID_GRAY)
        pdf.multi_cell(160, 5, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    pdf.ln(8)
    pdf.set_fill_color(*ACCENT_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(
        0,
        10,
        "  Contact us at hello@simplifyiq.ai  |  simplifyiq.ai  ",
        align="C",
        fill=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    safe_name = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in pdf_text(lead.company_name)).strip()
    safe_name = safe_name or "lead"
    filename = os.path.join(OUTPUT_DIR, f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_report.pdf")
    pdf.output(filename)
    logger.info("PDF saved: %s", filename)
    return filename
