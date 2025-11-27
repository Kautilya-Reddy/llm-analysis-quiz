import time
import re
import requests
import pandas as pd
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def get_rendered_html(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
    return html


def extract_submit_url_from_html(html: str, base_url: str):
    urls = re.findall(r"https?://[^\s\"']+", html)
    for u in urls:
        if "submit" in u.lower():
            return u

    m = re.search(r"(\/[^\s\"']*submit[^\s\"']*)", html, re.I)
    if m:
        return urljoin(base_url, m.group(1))

    # Absolute fallback (demo usually uses /submit)
    return urljoin(base_url, "/submit")


def compute_sum_from_html_table(html: str):
    try:
        tables = pd.read_html(html)
    except Exception:
        return 0.0

    if not tables:
        return 0.0

    df = tables[0]

    # Convert everything to numeric where possible
    df = df.apply(pd.to_numeric, errors="coerce")

    numeric_cols = df.select_dtypes(include="number").columns

    if not len(numeric_cols):
        return 0.0

    # Choose the column with the maximum variance (safest for demo)
    best_col = max(numeric_cols, key=lambda c: df[c].var(skipna=True))

    return float(df[best_col].sum(skipna=True))


def solve_single_page(url: str):
    try:
        html = get_rendered_html(url)
        submit_url = extract_submit_url_from_html(html, url)
        answer = compute_sum_from_html_table(html)
        return submit_url, answer
    except Exception:
        # Absolute safety net — NEVER crash
        return urljoin(url, "/submit"), 0.0


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
