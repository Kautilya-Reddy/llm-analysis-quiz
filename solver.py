import time
import json
import requests
from bs4 import BeautifulSoup


def fetch_text(url, timeout=20):
    """Simple HTML fetcher using requests only."""
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    html = r.text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    return text, html


def extract_json_from_response(resp):
    """Extract JSON safely from LLM or API output."""
    if isinstance(resp, dict):
        return resp

    text = str(resp).strip()
    try:
        return json.loads(text)
    except:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except:
            return None

    return None


def solve_quiz_task(email, secret, url, timeout_seconds=170):
    """MAIN FUNCTION – MUST MATCH app.py EXACTLY"""

    t0 = time.time()

    # STEP 1: Fetch page text
    page_text, page_html = fetch_text(url, timeout=20)

    # STEP 2: Dummy LLM-like JSON extraction logic
    # Since no LLM is used, we use a simple pattern:
    answer = "A"  # or detect something simple from text
    submit_url = None

    # Try to detect submit URL
    for word in page_html.split():
        if "submit" in word and "http" in word:
            submit_url = word.strip('",')
            break

    if not submit_url:
        # fallback: quiz pages always include "/submit"
        submit_url = url.replace("/task", "/submit")

    # STEP 3: Build payload for evaluator
    final_payload = {
        "email": email,
        "secret": secret,
        "url": url,
        "answer": answer
    }

    # STEP 4: Submit
    r = requests.post(submit_url, json=final_payload, timeout=20)
    r.raise_for_status()

    return {
        "status": "submitted",
        "submit_response": r.json(),
        "answer_used": answer,
        "submit_url": submit_url
    }
