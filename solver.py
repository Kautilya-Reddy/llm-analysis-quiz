import time
import base64
import re
import requests
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def extract_decoded_payload(html: str) -> str:
    match = re.search(r"atob\(`([^`]+)`\)", html)
    if not match:
        return ""

    b64 = match.group(1).replace("\n", "")
    decoded = base64.b64decode(b64).decode("utf-8", errors="ignore")
    return decoded


def find_submit_url_from_payload(payload: str) -> str | None:
    match = re.search(r"https://[^\s\"']+/submit", payload)
    return match.group(0) if match else None


def extract_numeric_answer(payload: str):
    numbers = re.findall(r"-?\d+\.?\d*", payload)
    if not numbers:
        return True

    if len(numbers) == 1:
        if "." in numbers[0]:
            return float(numbers[0])
        return int(numbers[0])

    total = 0
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

    payload_text = extract_decoded_payload(html)
    submit_url = find_submit_url_from_payload(payload_text)
    answer = extract_numeric_answer(payload_text)

    return answer, submit_url


def solve_quiz(email: str, secret: str, url: str):
    start_time = time.time()
    current_url = url
    last_result = None

    while current_url:
        if time.time() - start_time > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        answer, submit_url = solve_single_page(current_url)

        if not submit_url:
            return {"error": "submit_url_not_found"}

        payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer
        }

        r = requests.post(submit_url, json=payload, timeout=30)
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
