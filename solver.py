import time
import json
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def fetch_numbers_via_network(url: str):
    captured_payload = {}

    def handle_response(response):
        nonlocal captured_payload
        try:
            if "json" in response.headers.get("content-type", ""):
                data = response.json()
                if isinstance(data, dict) and "numbers" in data:
                    captured_payload = data
        except:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("response", handle_response)

        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        visible_text = page.evaluate("() => document.body.innerText")
        browser.close()

    return captured_payload, visible_text


def extract_submit_url(text: str, base_url: str):
    import re
    abs_urls = re.findall(r"https?://[^\s\"']+", text)
    for u in abs_urls:
        if "submit" in u.lower():
            return u

    if "/submit" in text:
        return urljoin(base_url, "/submit")

    return None


def compute_sum_from_payload(payload: dict):
    if "numbers" in payload and isinstance(payload["numbers"], list):
        return sum(payload["numbers"])
    return 0


def solve_quiz(email: str, secret: str, url: str):
    start_time = time.time()
    current_url = url
    last_result = None

    while current_url:
        if time.time() - start_time > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        payload, text = fetch_numbers_via_network(current_url)
        submit_url = extract_submit_url(text, current_url)

        if not submit_url:
            return {
                "error": "submit_url_not_found",
                "debug_payload_excerpt": text[:400]
            }

        answer_value = compute_sum_from_payload(payload)

        submit_payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer_value
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
