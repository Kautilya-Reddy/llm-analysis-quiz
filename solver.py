import time
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def fetch_network_json(url: str):
    captured = {}

    def handle_response(response):
        nonlocal captured
        try:
            ct = response.headers.get("content-type", "")
            if "application/json" in ct:
                data = response.json()
                if isinstance(data, dict):
                    captured = data
        except:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("response", handle_response)

        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(6000)

        visible_text = page.evaluate("() => document.body.innerText")
        browser.close()

    return captured, visible_text


def extract_submit_url(text: str, base_url: str):
    import re
    abs_urls = re.findall(r"https?://[^\s\"']+", text)
    for u in abs_urls:
        if "submit" in u.lower():
            return u

    if "/submit" in text:
        return urljoin(base_url, "/submit")

    return None


def solve_quiz(email: str, secret: str, url: str):
    payload, text = fetch_network_json(url)
    submit_url = extract_submit_url(text, url)

    return {
        "debug_network_payload": payload,
        "submit_url": submit_url,
        "visible_text_excerpt": text[:300]
    }
