import time
import requests
from bs4 import BeautifulSoup

def fetch_page_text(url, timeout=20):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.get_text("\n"), r.text

def call_llm_api(llm_api, prompt, secret):
    r = requests.post(
        llm_api,
        json={"secret": secret, "prompt": prompt},
        timeout=40
    )
    return r.json()

def solve_quiz_task(
    email,
    quiz_url,
    secret,
    llm_api=None,
    timeout_seconds=60
):
    start = time.time()
    
    page_text, page_html = fetch_page_text(quiz_url, timeout=20)
    
    prompt = f"""
You are solving an IITM LLM Analysis Quiz.

User email: {email}

Page text:
{page_text}

HTML content:
{page_html}

Give only the final answer.
"""

    if not llm_api:
        return {"error": "llm_api_missing"}

    response = call_llm_api(llm_api, prompt, secret)

    return {
        "email": email,
        "answer": response,
        "time_taken": time.time() - start
    }
