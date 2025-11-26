import time
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

TIME_LIMIT = 170  # seconds

def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script", "style"]):
        s.decompose()
    return soup.get_text(separator=" ", strip=True)

def find_submit_url(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for form in soup.find_all("form"):
        if form.get("action"):
            return form["action"]
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and "submit" in href.lower():
            return href
    return None

def solve_single_page(url: str) -> tuple[str | int | float | bool, str | None]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()
        text = extract_visible_text(html)
        submit_url = find_submit_url(html)

        browser.close()

    # ✅ Minimal generic "analysis fallback"
    # (Real tasks usually need custom logic later)
    answer = None

    for token in text.split():
        if token.replace(".", "", 1).isdigit():
            answer = float(token) if "." in token else int(token)
            break

    if answer is None:
        answer = True

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
