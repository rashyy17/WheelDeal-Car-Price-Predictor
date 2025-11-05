# src/scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urlencode
from tqdm import tqdm

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def clean_price(text):
    if not text or not isinstance(text, str):
        return None
    t = re.sub(r"[^\d]", "", text)
    try:
        return int(t) if t else None
    except:
        return None

def clean_km(text):
    if not text or not isinstance(text, str):
        return None
    t = re.sub(r"[^\d]", "", text)
    try:
        return int(t) if t else None
    except:
        return None

import requests
import random
import time
from urllib.parse import urlencode

# add or replace your HEADERS constant with this:
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}

def fetch_html(url, params=None, timeout=15, max_retries=3):
    """
    Fetch a webpage with retry, random delay, and realistic browser headers.
    """
    if params:
        url = url + "?" + urlencode(params)

    for attempt in range(max_retries):
        try:
            # random short delay to mimic human browsing
            time.sleep(random.uniform(1.0, 2.5))

            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()

            # check if response looks valid
            if "<html" not in r.text.lower():
                raise ValueError("Non-HTML response received")

            return r.text

        except Exception as e:
            print(f"⚠️ Attempt {attempt+1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                # wait longer before next retry
                time.sleep(random.uniform(2, 5))
                continue
            else:
                print("❌ Giving up on", url)
                return None


def parse_listings_from_html(html, site_hint=None):
    """
    Generic parser that attempts to extract title, price, kms, and some details.
    For best results, inspect the target site's HTML and adjust selectors below.
    """
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Candidate listing containers (try several common patterns)
    possible_containers = [
        ("li", {"class": re.compile(r".*listing.*|.*result.*|.*item.*", re.I)}),
        ("div", {"class": re.compile(r".*listing.*|.*result.*|.*card.*|.*EIR5N.*", re.I)}),
        ("article", {}),
        ("div", {"data-aut-id": "itemBox"})
    ]

    containers = []
    for tag, attrs in possible_containers:
        found = soup.find_all(tag, attrs=attrs)
        if found:
            containers = found
            break

    # fallback: find many <a> elements that look like listing links
    if not containers:
        containers = soup.find_all("a", href=True)
        containers = [c for c in containers if c.text.strip() and len(c.text.strip()) < 200][:200]

    for c in containers:
        text = c.get_text(" ", strip=True)

        # try to find price inside container
        price_candidates = c.find_all(text=re.compile(r"₹|\bINR\b|Rs\.|rs\.|\d{2,}"))
        price = None
        for pc in price_candidates:
            val = clean_price(pc)
            if val:
                price = val
                break

        # kms candidate
        km_candidates = c.find_all(text=re.compile(r"\d[\d,]*\s*km|\d[\d,]*\s*kms", re.I))
        km_val = None
        for kc in km_candidates:
            val = clean_km(kc)
            if val:
                km_val = val
                break

        # title: try heading tags inside container then fallback to text snippet
        title = None
        for tag in ("h2", "h3", "h1", "a", "span", "div"):
            t = c.find(tag)
            if t and len(t.get_text(strip=True)) > 3:
                title = t.get_text(strip=True)
                break
        if not title:
            title = (text[:120] + "...") if text else None

        # attempt to find year using 4-digit pattern like 2015/2019
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        year = int(year_match.group(0)) if year_match else None

        results.append({
            "title": title,
            "price": price,
            "km": km_val,
            "year": year,
            "raw_text": text
        })

    return pd.DataFrame(results)

def scrape_search_results(base_search_url, query_params=None, pages=1, delay=1.0):
    """
    Fetch multiple pages of search results (generic).
    base_search_url: the search URL for the target site, e.g. 'https://www.example.com/search'
    query_params: dict of query parameters used by the site
    pages: number of pages to fetch
    delay: seconds to wait between page requests (be polite!)
    """
    all_rows = []
    for page in range(1, pages+1):
        params = dict(query_params or {})
        # many sites use 'page' or 'p' param; adapt as needed
        params.update({"page": page})
        html = fetch_html(base_search_url, params=params)
        if not html:
            continue
        df_page = parse_listings_from_html(html)
        if not df_page.empty:
            all_rows.append(df_page)
        time.sleep(delay)

    if all_rows:
        combined = pd.concat(all_rows, ignore_index=True)
        # drop rows without price as a basic filter
        combined = combined.dropna(subset=["price"]).reset_index(drop=True)
        return combined
    else:
        return pd.DataFrame(columns=["title", "price", "km", "year", "raw_text"])


# Example helpers for specific sites (skeletons you must adapt after inspecting HTML)
def scrape_cardekho_model(model_name, pages=2, delay=1.0):
    """
    Example function for CarDekho — you must inspect CarDekho's search URL & params and update.
    For CarDekho, a search URL might look like:
        https://www.cardekho.com/used-cars+{model_name}
    or a specific search endpoint. Inspect and replace `base_search_url`.
    """
    base_search_url = f"https://www.cardekho.com/used-cars/{model_name.replace(' ', '-')}"
    return scrape_search_results(base_search_url, query_params={}, pages=pages, delay=delay)


def scrape_olx_model(model_name, pages=2, delay=1.0):
    base_search_url = f"https://www.olx.in/items/q-{model_name.replace(' ', '-')}"
    return scrape_search_results(base_search_url, query_params={}, pages=pages, delay=delay)
