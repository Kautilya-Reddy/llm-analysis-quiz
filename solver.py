import requests
from bs4 import BeautifulSoup

def render_url_text(url, timeout=30):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    return text, html


def solve_quiz_task(email, url, llm_api, timeout_seconds=60):
    """
    Main solver used by Render & evaluator.
    """

    page_text, page_html = render_url_text(url)

    prompt = (
        "You are an AI solver for quiz tasks.\n"
        "Extract the quiz question and provide the correct answer.\n\n"
        f"PAGE TEXT:\n{page_text}"
    )

    # Call LLM
    r = requests.post(
        llm_api,
        json={
            "model": "gpt-4o-mini",
            "input": prompt,
        },
        timeout=timeout_seconds - 5
    )

    r.raise_for_status()

    answer = r.json()

    return {
        "email": email,
        "answer": answer
    }
