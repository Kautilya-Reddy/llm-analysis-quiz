import time
import base64
import re
import requests
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def extract_decoded_payload_from_html(html: str) -> str:
    match = re.search(r"atob\((?:`|'|\")([^`'\"]+)(?:`|'|\")\)", html, re.DOTALL)
    if not match:
        return ""

    b64 = match.group(1).replace("\n", "")
    try:
        decoded = base64.b64decode(b64).decode("utf-8", errors="ignore")
    except Exception:
        decoded = ""
    return decoded


def extract_visible_text_from_dom(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)
        text = page.inner_text("body")
        browser.close()
    return text


def find_submit_url(text: str) -> str | None:
    urls = re.findall(r"https?://[^\s\"']+", text)
    if not urls:
        return None

    for u in urls:
        if "submit" in u.lower():
            return u

    return urls[0]


def extract_numeric_answer(text: str):
    numbers = re.findall(r"-?\d+\.?\d*", text)
    if not numbers:
        return True

    if len(numbers) == 1:
        return float(numbers[0]) if "." in numbers[0] else int(numbers[0])

    total = 0.0
    for n in numbers:
        total += float(n)
    return total


def solve_single_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)
        html = page.content()
        browser.close()

    payload_text = extract_decoded_payload_from_html(html)

    if not payload_text.strip():
        payload_text = extract_visible_text_from_dom(url)

    submit_url = find_submit_url(payload_text)
    answer = extract_numeric_answer(payload_text)

    return answer, submit_url, payload_text


def solve_quiz(email: str, secret: str, url: str):
    start_time = time.time()
    current_url = url
    last_result = None

    while current_url:
        if time.time() - start_time > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        answer, submit_url, payload_text = solve_single_page(current_url)

        if not submit_url:
            return {
                "error": "submit_url_not_found",
                "debug_payload_excerpt": payload_text[:300]
            }

        submit_payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer
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
