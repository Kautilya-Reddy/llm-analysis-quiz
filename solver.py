import time
import re
import requests
import pandas as pd
import html as html_lib
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
        content = page.content()
        browser.close()
    return content


def clean_url(u: str):
    u = html_lib.unescape(u)
    u = u.strip().replace("<", "").replace(">", "")
    return u


def extract_submit_url_from_html(html_str: str, base_url: str):
    raw_urls = re.findall(r"https?://[^\s\"'>]+", html_str)

    for u in raw_urls:
        u = clean_url(u)
        if "submit" in u.lower():
            return u

    m = re.search(r"(/[^\"'>\s]*submit[^\"'>\s]*)", html_str, re.I)
    if m:
        return urljoin(base_url, clean_url(m.group(1)))

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

    best_col = max(numeric_cols, key=lambda c: df[c].var(skipna=True))
    return float(df[best_col].sum(skipna=True))


def safe_json_response(resp):
    try:
        return resp.json()
    except Exception:
        return {
            "raw_text": resp.text[:500],
            "status_code": resp.status_code
        }


def solve_single_page(url: str):
    try:
        html_content = get_rendered_html(url)
        submit_url = extract_submit_url_from_html(html_content, url)
        answer = compute_sum_from_html_table(html_content)
        return submit_url, answer
    except Exception:
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

        try:
            r = requests.post(submit_url, json=payload, timeout=30)
            response = safe_json_response(r)
        except Exception as e:
            return {
                "error": "submit_request_failed",
                "detail": str(e)
            }

        last_response = response

        if isinstance(response, dict) and "url" in response and response["url"]:
            current_url = response["url"]
        else:
            break

    return last_response
