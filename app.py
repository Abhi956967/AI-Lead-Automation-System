"""
app.py
───────
SimplifIQ Lead Automation — Streamlit Frontend
Run with:  streamlit run app.py
"""

import os
import time
import logging
import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="SimplifIQ | Lead Intelligence",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Font + base */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Hero */
  .hero-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 10px;
  }
  .hero-title {
    font-size: 32px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.25;
    margin-bottom: 6px;
  }
  .hero-sub {
    font-size: 15px;
    color: #64748b;
    margin-bottom: 28px;
    line-height: 1.6;
  }

  /* Cards */
  .step-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .step-num {
    background: #1d4ed8;
    color: white;
    width: 24px; height: 24px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
    flex-shrink: 0;
  }

  /* Success banner */
  .success-box {
    background: linear-gradient(135deg, #d1fae5 0%, #ecfdf5 100%);
    border: 1px solid #6ee7b7;
    border-radius: 12px;
    padding: 24px 28px;
    margin-top: 20px;
  }
  .success-title { font-size: 20px; font-weight: 700; color: #065f46; margin-bottom: 6px; }
  .success-sub   { font-size: 14px; color: #047857; }

  /* Form styling */
  .stTextInput > label, .stSelectbox > label, .stTextArea > label {
    font-weight: 500 !important;
    font-size: 13px !important;
    color: #374151 !important;
  }
  .stButton > button {
    background: #1d4ed8 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    width: 100% !important;
    transition: background 0.2s !important;
  }
  .stButton > button:hover {
    background: #1e40af !important;
  }

  /* Progress labels */
  .progress-label {
    font-size: 13px;
    color: #1d4ed8;
    font-weight: 500;
    margin-top: -8px;
    margin-bottom: 12px;
  }

  /* Divider */
  .section-divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 24px 0;
  }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Get your free key at console.groq.com",
    )
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

    st.markdown("---")
    st.markdown("**Email Settings**")
    email_method = st.selectbox("Method", ["smtp", "sendgrid"], index=0)
    os.environ["EMAIL_METHOD"] = email_method

    if email_method == "smtp":
        smtp_email = st.text_input("Gmail Address", value=os.getenv("SMTP_EMAIL", ""))
        smtp_pass  = st.text_input("App Password", type="password", value=os.getenv("SMTP_PASSWORD", ""))
        if smtp_email: os.environ["SMTP_EMAIL"] = smtp_email
        if smtp_pass:  os.environ["SMTP_PASSWORD"] = smtp_pass
    else:
        sg_key   = st.text_input("SendGrid API Key", type="password", value=os.getenv("SENDGRID_API_KEY", ""))
        sg_email = st.text_input("Sender Email", value=os.getenv("SENDER_EMAIL", ""))
        if sg_key:   os.environ["SENDGRID_API_KEY"] = sg_key
        if sg_email: os.environ["SENDER_EMAIL"] = sg_email

    st.markdown("---")
    st.markdown("**Bonus Features (optional)**")
    use_google = st.checkbox("Enable Google Drive + Sheets")
    if use_google:
        sa_json = st.text_input("Service Account JSON path", value=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", ""))
        drive_folder = st.text_input("Drive Folder ID", value=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""))
        sheet_id = st.text_input("Google Sheet ID", value=os.getenv("GOOGLE_SHEET_ID", ""))
        if sa_json:     os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = sa_json
        if drive_folder: os.environ["GOOGLE_DRIVE_FOLDER_ID"] = drive_folder
        if sheet_id:    os.environ["GOOGLE_SHEET_ID"] = sheet_id

    st.markdown("---")
    st.caption("SimplifIQ v1.0 · Built with Groq + Streamlit")


# ── Hero ─────────────────────────────────────────────────────────────
st.markdown('<div class="hero-badge">🤖 AI-Powered</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Lead Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown(
    "<div class=\"hero-sub\">Submit a prospect&#39;s details and our AI instantly researches their "
    "company, generates a personalized audit report, and delivers it \u2014 all automatically.</div>",
    unsafe_allow_html=True
)

# How it works
col1, col2, col3, col4 = st.columns(4)
steps = [
    ("1", "Submit", "Fill in company details"),
    ("2", "Enrich", "We research the company"),
    ("3", "Generate", "AI writes the report"),
    ("4", "Deliver", "PDF sent by email"),
]
for col, (num, title, desc) in zip([col1, col2, col3, col4], steps):
    with col:
        st.markdown(f"""
        <div style="text-align:center; padding:10px 4px;">
          <div style="background:#1d4ed8;color:white;width:28px;height:28px;border-radius:50%;
                      display:flex;align-items:center;justify-content:center;
                      font-size:12px;font-weight:700;margin:0 auto 8px;">{num}</div>
          <div style="font-size:13px;font-weight:600;color:#0f172a;">{title}</div>
          <div style="font-size:11px;color:#94a3b8;margin-top:3px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Lead Form ────────────────────────────────────────────────────────
st.markdown("#### 📋 Prospect Information")

with st.form("lead_form", clear_on_submit=False):
    col_a, col_b = st.columns(2)
    with col_a:
        full_name = st.text_input("Full Name *", placeholder="e.g. Priya Sharma")
        company_name = st.text_input("Company Name *", placeholder="e.g. Acme Corp")
        company_website = st.text_input("Company Website", placeholder="e.g. acme.com")
        industry = st.selectbox(
            "Industry",
            ["", "SaaS / Software", "Finance & Banking", "Healthcare", "Consulting",
             "E-commerce / Retail", "Manufacturing", "Real Estate", "Education",
             "Marketing & Media", "Logistics", "Legal", "Other"],
        )
    with col_b:
        email = st.text_input("Work Email *", placeholder="e.g. priya@acme.com")
        job_title = st.text_input("Job Title *", placeholder="e.g. Head of Operations")
        company_size = st.selectbox(
            "Company Size",
            ["", "1–10", "11–50", "51–200", "201–500", "501–1000", "1000+"],
        )
        pain_points = st.text_input(
            "Key Challenge / Pain Point",
            placeholder="e.g. Manual lead qualification takes too long"
        )

    message = st.text_area(
        "Additional Context (optional)",
        placeholder="Tell us more about your current workflow or goals...",
        height=80,
    )

    submitted = st.form_submit_button("⚡ Generate Intelligence Report", use_container_width=True)


# ── Pipeline Execution ───────────────────────────────────────────────
if submitted:
    # Basic validation
    errors = []
    if not full_name.strip():    errors.append("Full name is required.")
    if not email.strip():        errors.append("Work email is required.")
    if not company_name.strip(): errors.append("Company name is required.")
    if not job_title.strip():    errors.append("Job title is required.")
    if not os.getenv("GROQ_API_KEY"):
        errors.append("Groq API key is required. Set it in the sidebar.")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    # Import pipeline
    from modules.models import LeadInput
    from modules.workflow import run_pipeline

    try:
        lead_input = LeadInput(
            full_name=full_name.strip(),
            email=email.strip(),
            company_name=company_name.strip(),
            company_website=company_website.strip() or None,
            job_title=job_title.strip(),
            company_size=company_size or None,
            industry=industry or None,
            pain_points=pain_points.strip() or None,
            message=message.strip() or None,
        )
    except ValidationError as e:
        for err in e.errors():
            st.error(f"Validation error: {err['msg']}")
        st.stop()

    # Progress UI
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(f"#### 🔄 Processing report for **{company_name}**")

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_ui(pct: float, msg: str):
        progress_bar.progress(pct)
        status_text.markdown(f'<div class="progress-label">⏳ {msg}</div>', unsafe_allow_html=True)
        time.sleep(0.1)

    try:
        result = run_pipeline(lead_input, progress_callback=update_ui)

        # Success state
        progress_bar.progress(1.0)
        status_text.empty()

        st.markdown(f"""
        <div class="success-box">
          <div class="success-title">✅ Report Delivered Successfully!</div>
          <div class="success-sub">
            The personalized audit report for <strong>{result.company_name}</strong>
            has been sent to <strong>{result.email}</strong>.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Show summary
        st.markdown("---")
        st.markdown("#### 📄 Report Summary")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Company:** {result.company_name}")
            st.markdown(f"**Contact:** {result.full_name}")
            st.markdown(f"**Email:** {result.email}")
            st.markdown(f"**Industry:** {result.industry or 'N/A'}")
        with col2:
            st.markdown(f"**Status:** {result.report_status}")
            st.markdown(f"**Generated at:** {result.submitted_at}")
            if result.drive_link:
                st.markdown(f"**[📁 View on Drive]({result.drive_link})**")
            if result.pdf_path:
                with open(result.pdf_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download PDF Report",
                        f,
                        file_name=f"{result.company_name}_report.pdf",
                        mime="application/pdf",
                    )

        if result.executive_summary:
            st.markdown("**Executive Summary:**")
            st.info(result.executive_summary)

    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        st.markdown("**Tip:** Check the sidebar settings and ensure your API keys are correct.")
        logging.exception("Pipeline failed")

# ── Footer ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-size:12px;color:#94a3b8;">'
    'SimplifIQ Intelligence Platform · Powered by Groq + LLaMA 3.3 70B · Built for the AI era'
    '</div>',
    unsafe_allow_html=True
)