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
    m = re.search(r"atob\(`([^`]*)`\)", html)
    if not m:
        raise ValueError("No base64 payload found")
    return m.group(1)


def solve_base64_table(payload: str):
    decoded = base64.b64decode(payload).decode("utf-8", errors="ignore")

    lines = decoded.strip().splitlines()
    rows = []

    for line in lines:
        if "," in line:
            parts = [p.strip() for p in line.split(",")]
            rows.append(parts)

    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.apply(pd.to_numeric, errors="coerce")

    numeric_col = df.select_dtypes(include="number").columns[0]
    return float(df[numeric_col].sum())


def solve_single_page(url: str):
    text, html = get_rendered_text_and_html(url)
    submit_url = extract_submit_url(text, url)

    payload = extract_base64_payload(html)
    answer = solve_base64_table(payload)

    return submit_url, answer


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
