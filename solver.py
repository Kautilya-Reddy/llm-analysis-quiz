import time
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def extract_text_from_dom(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)
        text = page.inner_text("body")
        browser.close()
    return text


def extract_submit_url(text: str, base_url: str):
    for line in text.splitlines():
        if "/submit" in line:
            return urljoin(base_url, "/submit")

    return None


def solve_quiz(email: str, secret: str, url: str):
    text = extract_text_from_dom(url)
    submit_url = extract_submit_url(text, url)

    return {
        "debug_full_text": text[:4000],
        "submit_url_found": submit_url
    }
