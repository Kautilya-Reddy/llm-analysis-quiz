import time
import base64
import re
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def extract_text_and_urls_from_dom(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        html = page.content()
        text = page.inner_text("body")

        browser.close()

    return html, text


def extract_relative_or_absolute_urls(text: str):
    abs_urls = re.findall(r"https?://[^\s\"']+", text)
    rel_urls = re.findall(r"/[a-zA-Z0-9\-\_/\\?=&]+", text)
    return abs_urls + rel_urls


def extract_demo_scrape_url(text: str):
    match = re.search(r"/demo-scrape-data\?[^\s]+", text)
    return match.group(0) if match else None


def extract_submit_url(text: str):
    match = re.search(r"/submit", text)
    return match.group(0) if match else None


def scrape_secret_from_demo(scrape_url: str):
    r = requests.get(scrape_url, timeout=30)
    r.raise_for_status()
    text = r.text.strip()

    code_match = re.search(r"[A-Za-z0-9]{4,}", text)
    return code_match.group(0)


def solve_single_page(url: str, email: str):
    html, visible_text = extract_text_and_urls_from_dom(url)

    scrape_url = extract_demo_scrape_url(visible_text)
    submit_url = extract_submit_url(visible_text)

    if scrape_url:
        scrape_url = urljoin(url, scrape_url)

    if submit_url:
        submit_url = urljoin(url, submit_url)

    secret_code = None
    if scrape_url:
        secret_code = scrape_secret_from_demo(scrape_url)

    return secret_code, submit_url, visible_text


def solve_quiz(email: str, secret: str, url: str):
    start_time = time.time()
    current_url = url
    last_result = None

    while current_url:
        if time.time() - start_time > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        secret_code, submit_url, text = solve_single_page(current_url, email)

        if not submit_url:
            return {
                "error": "submit_url_not_found",
                "debug_payload_excerpt": text[:400]
            }

        if not secret_code:
            return {
                "error": "scraped_secret_not_found",
                "debug_payload_excerpt": text[:400]
            }

        submit_payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": secret_code
        }

        r = requests.post(submit_url, json=submit_payload, timeout=30)
        r.raise_for_status()
        response = r.json()

        last_result = response

        if not response.get("correct", False):
            if "url" in response:
                current_url = response["url"]
                continue
            else:
                break
        else:
            if "url" in response:
                current_url = response["url"]
                continue
            else:
                break

    return last_result
