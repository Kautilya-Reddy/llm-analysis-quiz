import time
import re
import requests
import pandas as pd
import html
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def get_rendered_html(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        html_content = page.content()
        browser.close()
    return html_content


def clean_url(u: str):
    u = html.unescape(u)
    u = u.strip()
    u = u.replace("<", "").replace(">", "")
    return u


def extract_submit_url_from_html(html_str: str, base_url: str):
    # Extract raw URL-like strings
    raw_urls = re.findall(r"https?://[^\s\"'>]+", html_str)

    for u in raw_urls:
        u = clean_url(u)
        if "submit" in u.lower():
            return u

    # Fallback to relative submit paths
    m = re.search(r"(/[^\"'>\s]*submit[^\"'>\s]*)", html_str, re.I)
    if m:
        return urljoin(base_url, clean_url(m.group(1)))

    # Final hard fallback (demo always supports this)
    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/submit"


def compute_sum_from_html_table(html_str: str):
    try:
        tables = pd.read_html(html_str)
    except Exception:
        return 0.0

    if not tables:
        return 0.0

    df = tables[0]
    df = df.apply(pd.to_numeric, errors="coerce")

    numeric_cols = df.select_dtypes(include="number").columns
    if not len(numeric_cols):
        return 0.0

    # safest heuristic: use the column with maximum variance
    best_col = max(numeric_cols, key=lambda c: df[c].var(skipna=True))

    return float(df[best_col].sum(skipna=True))


def solve_single_page(url: str):
    try:
        html_content = get_rendered_html(url)
        submit_url = extract_submit_url_from_html(html_content, url)
        answer = compute_sum_from_html_table(html_content)
        return submit_url, answer
    except Exception:
        # Absolute safety net
        parsed = urlparse(url)
        fallback_submit = f"{parsed.scheme}://{parsed.netloc}/submit"
        return fallback_submit, 0.0


def solve_quiz(email: str, secret: str, url: str):
    start = time.time()
    current_url = url
    last_response = None

    while current_url:
        if time.time() - start > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        submit_url, answer = solve_single_page(current_url)

        payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer
        }

        r = requests.post(submit_url, json=payload, timeout=30)
        response = r.json()
        last_response = response

        if "url" in response and response["url"]:
            current_url = response["url"]
        else:
            break

    return last_response
