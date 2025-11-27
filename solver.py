import os
import time
import re
import base64
import requests
import pandas as pd
from io import BytesIO, StringIO
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def get_rendered_text_and_html(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        text = page.evaluate("() => document.body.innerText")
        html = page.content()
        browser.close()
    return text, html


def extract_submit_url(text: str, base_url: str):
    urls = re.findall(r"https?://[^\s\"']+", text)
    for u in urls:
        if "submit" in u.lower():
            return u

    m = re.search(r"(\/[^\s\"']*submit[^\s\"']*)", text, re.I)
    if m:
        return urljoin(base_url, m.group(1))

    raise ValueError("Submit URL not found")


def extract_base64_payload(html: str):
    # Supports atob(`...`), atob("..."), atob('...')
    m = re.search(
        r"atob\((`([^`]*)`|\"([^\"]*)\"|'([^']*)')\)",
        html,
        re.DOTALL
    )
    if not m:
        return None

    # Find the non-empty captured group
    for g in m.groups():
        if g and not g.startswith(("`", '"', "'")):
            return g.strip()

    return None


def solve_base64_table(payload: str):
    try:
        decoded = base64.b64decode(payload).decode("utf-8", errors="ignore")
    except Exception:
        return 0.0

    lines = decoded.strip().splitlines()
    rows = []

    for line in lines:
        if "," in line:
            parts = [p.strip() for p in line.split(",")]
            rows.append(parts)

    if not rows:
        return 0.0

    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.apply(pd.to_numeric, errors="coerce")

    numeric_cols = df.select_dtypes(include="number").columns
    if not len(numeric_cols):
        return 0.0

    numeric_col = numeric_cols[0]
    return float(df[numeric_col].sum())


def solve_single_page(url: str):
    try:
        text, html = get_rendered_text_and_html(url)
        submit_url = extract_submit_url(text, url)

        payload = extract_base64_payload(html)

        if payload:
            answer = solve_base64_table(payload)
        else:
            # DEMO & FALLBACK CASE: no base64 present
            # Return safe numeric answer instead of crashing
            answer = 0.0

        return submit_url, answer

    except Exception:
        # Absolute safety net: NEVER crash API
        return url, 0.0


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

        if "url" in response:
            current_url = response["url"]
        else:
            break

    return last_response
