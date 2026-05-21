"""
modules/enrichment.py
──────────────────────
Scrapes company data from website + Google search fallback.
Returns structured enrichment data to populate EnrichedLead.
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Optional
from urllib.parse import urlparse, urljoin
import time

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

TIMEOUT = 10


def safe_get(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    tag = soup.find("meta", attrs={"property": "og:description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def extract_about_text(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """
    Try to get meaningful 'about us' text from the homepage
    or a linked about page.
    """
    # Try inline paragraphs first
    for section in soup.find_all(["section", "div"], class_=re.compile(r"about|hero|intro|mission", re.I)):
        paras = section.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 40)
        if len(text) > 100:
            return text[:800]

    # Try standalone paragraphs
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 60]
    if paras:
        return " ".join(paras[:3])[:800]

    return None


def extract_social_links(soup: BeautifulSoup) -> str:
    socials = {}
    patterns = {
        "LinkedIn": r"linkedin\.com",
        "Twitter/X": r"twitter\.com|x\.com",
        "Facebook": r"facebook\.com",
        "YouTube": r"youtube\.com",
    }
    for a in soup.find_all("a", href=True):
        href = a["href"]
        for platform, pattern in patterns.items():
            if re.search(pattern, href, re.I) and platform not in socials:
                socials[platform] = href.strip()
    return ", ".join(f"{k}: {v}" for k, v in socials.items()) if socials else "Not found"


def extract_tech_hints(soup: BeautifulSoup) -> Optional[str]:
    """Check script/link tags for common tech stack indicators."""
    scripts = [s.get("src", "") for s in soup.find_all("script", src=True)]
    links = [l.get("href", "") for l in soup.find_all("link", href=True)]
    all_refs = " ".join(scripts + links).lower()

    detected = []
    checks = {
        "React": "react",
        "Vue.js": "vue",
        "Angular": "angular",
        "Next.js": "next",
        "WordPress": "wp-content",
        "Shopify": "shopify",
        "HubSpot": "hubspot",
        "Segment": "segment",
        "Salesforce": "salesforce",
        "Intercom": "intercom",
        "Zendesk": "zendesk",
        "Google Analytics": "gtag",
        "Hotjar": "hotjar",
        "Stripe": "stripe",
    }
    for name, keyword in checks.items():
        if keyword in all_refs:
            detected.append(name)

    return ", ".join(detected) if detected else None


def scrape_news(company_name: str) -> Optional[str]:
    """
    Try to get recent news about the company via Google News RSS.
    This is a free, no-API-key approach.
    """
    try:
        query = company_name.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item")[:3]
        news_items = []
        for item in items:
            title = item.find("title")
            if title:
                news_items.append(title.get_text(strip=True))
        return "; ".join(news_items) if news_items else None
    except Exception as e:
        logger.warning(f"News scrape failed: {e}")
        return None


def enrich_company(company_name: str, website: Optional[str] = None) -> dict:
    """
    Main enrichment function. Returns a dict of enriched fields.
    Gracefully handles failures — always returns something.
    """
    result = {
        "company_description": None,
        "company_hq": None,
        "company_founded": None,
        "key_products_services": None,
        "recent_news": None,
        "tech_stack": None,
        "competitors": None,
        "social_links": None,
    }

    soup = None

    # 1. Try the company website
    if website:
        soup = safe_get(website)

    # 2. Fallback: guess the website from company name
    if not soup and company_name:
        guessed = "https://www." + company_name.lower().replace(" ", "") + ".com"
        soup = safe_get(guessed)
        if soup:
            website = guessed

    # 3. Extract data from the page
    if soup:
        desc = extract_meta_description(soup)
        about = extract_about_text(soup, website or "")
        result["company_description"] = desc or about or "Could not extract description."
        result["social_links"] = extract_social_links(soup)
        tech = extract_tech_hints(soup)
        if tech:
            result["tech_stack"] = tech

        # Look for founding year
        year_match = re.search(r"(?:founded|established|since)\s+(?:in\s+)?(\d{4})", soup.get_text(), re.I)
        if year_match:
            result["company_founded"] = year_match.group(1)

        # Look for HQ / location
        loc_match = re.search(r"headquartered\s+in\s+([A-Za-z ,]+?)[\.\,]", soup.get_text(), re.I)
        if loc_match:
            result["company_hq"] = loc_match.group(1).strip()

    # 4. Get recent news (always attempt)
    result["recent_news"] = scrape_news(company_name)

    # 5. Fallback description if still empty
    if not result["company_description"]:
        result["company_description"] = f"{company_name} is a company we were unable to fully profile at this time."

    return result
