# ⚡ SimplifIQ — AI Lead Automation System

> A fully automated pipeline that takes a prospect's company details, enriches them via web scraping, generates a personalized audit PDF using Groq's LLaMA 3.3 70B, and emails it — all without human intervention.

---

## 🗂️ Project Structure

```
lead_automation/
├── app.py                        ← Streamlit UI (entry point)
├── requirements.txt
├── .env.example                  ← Copy to .env and fill in
├── output/                       ← Generated PDFs saved here
└── modules/
    ├── models.py                 ← Pydantic data models
    ├── enrichment.py             ← Web scraping + company research
    ├── ai_insights.py            ← Groq LLM insight generation
    ├── pdf_generator.py          ← Professional PDF builder (FPDF2)
    ├── email_sender.py           ← SMTP / SendGrid email delivery
    ├── google_integration.py     ← Drive archival + Sheets logging (bonus)
    └── workflow.py               ← Pipeline orchestrator
```

---

## 🚀 Step-by-Step Setup

### Step 1 — Clone / Download the project

```bash
# If you have git:
git clone <your-repo-url>
cd lead_automation

# Or just download the zip and extract it
```

---

### Step 2 — Create a Python virtual environment

```bash
# Create venv
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> If you get lxml errors on Windows, use: `pip install lxml --only-binary :all:`

---

### Step 4 — Get your Groq API Key (FREE)

1. Go to **https://console.groq.com**
2. Sign up / log in
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key — you'll need it in Step 5

---

### Step 5 — Configure environment variables

```bash
# Copy the example file
cp .env.example .env

# Open .env in any text editor
notepad .env        # Windows
nano .env           # Mac/Linux
```

Fill in at minimum:
```
GROQ_API_KEY=gsk_your_key_here
EMAIL_METHOD=smtp
SMTP_EMAIL=yourgmail@gmail.com
SMTP_PASSWORD=your_app_password
```

#### 📧 Gmail App Password Setup (required for SMTP)
Gmail won't let you use your normal password. You need an **App Password**:
1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** if not already on
3. Search for "App Passwords" in the search bar
4. Create a new App Password for "Mail"
5. Copy the 16-character password → paste in `.env` as `SMTP_PASSWORD`

---

### Step 6 — Run the application

```bash
streamlit run app.py
```

Your browser will open at **http://localhost:8501**

---

### Step 7 — Submit a lead

1. Enter the prospect's name, email, company, job title
2. Optionally fill in website, industry, company size, pain points
3. Click **"Generate Intelligence Report"**
4. Watch the live progress bar as the pipeline runs
5. The prospect receives the PDF by email, and you can download it too

---

## 🎁 Bonus Features Setup

### Google Drive PDF Archival + Sheets Lead Tracker

#### 1. Create a Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **New Project** → give it a name
3. Enable these APIs:
   - **Google Drive API**
   - **Google Sheets API**
   (Search for each in the search bar, click Enable)

#### 2. Create a Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Give it a name (e.g. `lead-automation`)
4. Skip optional steps → click **Done**
5. Click on the service account → **Keys** tab
6. **Add Key** → **Create New Key** → **JSON**
7. Download the JSON file — save it somewhere safe (e.g. `credentials/service_account.json`)

#### 3. Set up Google Drive Folder

1. Go to **Google Drive** → create a new folder called `SimplifIQ Reports`
2. Right-click the folder → **Share**
3. Paste the service account email (found in the JSON file as `client_email`)
4. Give it **Editor** access → click Done
5. Open the folder and copy the **Folder ID** from the URL:
   `https://drive.google.com/drive/folders/THIS_IS_THE_FOLDER_ID`

#### 4. Set up Google Sheet

1. Go to **Google Sheets** → create a new blank spreadsheet
2. Name it `SimplifIQ Leads Tracker`
3. Share it with the service account email (Editor access)
4. Copy the **Sheet ID** from the URL:
   `https://docs.google.com/spreadsheets/d/THIS_IS_THE_SHEET_ID/edit`

#### 5. Update `.env`

```
GOOGLE_SERVICE_ACCOUNT_JSON=credentials/service_account.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_SHEET_ID=your_sheet_id
```

Or check **Enable Google Drive + Sheets** in the sidebar and paste the values there.

---

## 🔧 Configuration Reference

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | From console.groq.com |
| `EMAIL_METHOD` | ✅ Yes | `smtp` or `sendgrid` |
| `SMTP_EMAIL` | If SMTP | Your Gmail address |
| `SMTP_PASSWORD` | If SMTP | Gmail App Password (16 chars) |
| `SENDGRID_API_KEY` | If SendGrid | From app.sendgrid.com |
| `SENDER_EMAIL` | If SendGrid | Verified sender email |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Bonus | Path to service account JSON |
| `GOOGLE_DRIVE_FOLDER_ID` | Bonus | ID from Drive folder URL |
| `GOOGLE_SHEET_ID` | Bonus | ID from Sheet URL |

---

## 🏗️ Architecture & Design Decisions

### Why Groq?
- Groq offers the fastest LLM inference available (often <1s per call)
- `llama-3.3-70b-versatile` is free on the generous free tier
- Produces high-quality, nuanced business analysis

### Why FPDF2 over WeasyPrint / Puppeteer?
- Zero external system dependencies (no Chrome, no wkhtmltopdf)
- Works on any OS, in Docker, in any CI/CD pipeline
- FPDF2 gives precise pixel-level control over layout

### Why web scraping over a paid API?
- Keeps the solution zero-cost for the assessment
- Graceful fallback — if a site blocks scrapers, the LLM still generates insights

### Fallback Strategy
- Scraping fails → LLM uses only the form data
- LLM call fails → fallback text is used per section
- Email fails → PDF is still saved locally + downloadable from UI
- Google fails → non-critical, silently logged

---

## 🧪 Testing

```bash
# Quick smoke test without email
python -c "
from modules.models import LeadInput, EnrichedLead
from modules.enrichment import enrich_company
data = enrich_company('Notion', 'https://notion.so')
print(data)
"

# Test PDF generation
python -c "
import os; os.environ['GROQ_API_KEY'] = 'your_key'
from modules.models import EnrichedLead
from modules.pdf_generator import generate_pdf
lead = EnrichedLead(full_name='Test User', email='test@test.com', company_name='TestCo', company_website=None, job_title='CEO')
path = generate_pdf(lead)
print('PDF:', path)
"
```

---

## 📝 Assumptions & Tradeoffs

- **No prospect database** — each submission is stateless (the Sheet acts as the log)
- **Scraping is best-effort** — sites that block bots will return partial data; the LLM handles this gracefully
- **Email assumes English** — localization not implemented
- **FPDF2 uses built-in fonts** — no external font files needed, but font choice is limited to Helvetica/Courier/Times
- **Rate limiting** — Groq free tier has token limits; for high volume, add retry logic or upgrade

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `groq` | LLM API client |
| `fpdf2` | PDF generation |
| `beautifulsoup4` + `lxml` | Web scraping |
| `requests` | HTTP client |
| `pydantic` | Data validation |
| `python-dotenv` | Env var loading |
| `google-api-python-client` | Drive + Sheets (bonus) |
| `sendgrid` | Email (optional) |
