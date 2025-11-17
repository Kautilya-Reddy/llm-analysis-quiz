import requests
from bs4 import BeautifulSoup
import json
import time

# -------------------------------------------------
# Simple URL renderer without Playwright
# -------------------------------------------------
def render_url_text(url, timeout=10):
    """
    Fetch page HTML using requests, and extract visible text using BeautifulSoup.
    This works on Render without any browser dependencies.
    """
    response = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    response.raise_for_status()

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # Extract readable page text
    text = soup.get_text(separator="\n", strip=True)

    return text, html


# -------------------------------------------------
# Main quiz solver
# -------------------------------------------------
def solve_quiz_task(email, secret, url, timeout_seconds=40):
    """
    Main function called from /task in app.py.
    It fetches the target webpage, extracts text and HTML,
    and returns a JSON-friendly result dictionary.
    """

    start_time = time.time()

    # Fetch text & HTML from the provided URL
    text, html = render_url_text(url, timeout=min(10, timeout_seconds - 5))

    elapsed = round(time.time() - start_time, 2)

    # IMPORTANT:
    # The evaluator expects a dict containing:
    # - "email"
    # - "secret"
    # - "answer" (your extracted text or processed result)

    result = {
        "email": email,
        "secret": secret,
        "elapsed_time": elapsed,
        "answer": {
            "extracted_text": text[:5000],   # limit to avoid huge uploads
            "html_snippet": html[:5000]
        }
    }

    return result
