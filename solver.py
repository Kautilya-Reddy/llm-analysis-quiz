import os
import time
import re
import requests
import pandas as pd
from io import BytesIO
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import openai

TIME_LIMIT = 170

openai.api_key = os.getenv("OPENAI_API_KEY")


def get_rendered_text(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        text = page.evaluate("() => document.body.innerText")
        browser.close()
    return text


def extract_submit_url(text: str, base_url: str):
    urls = re.findall(r"https?://[^\s\"']+", text)
    for u in urls:
        if "submit" in u.lower():
            return u

    if "/submit" in text.lower():
        return urljoin(base_url, "/submit")

    raise ValueError("Submit URL not found")


def extract_file_urls(text: str):
    return [
        u for u in re.findall(r"https?://[^\s\"']+", text)
        if any(ext in u.lower() for ext in [".csv", ".xlsx"])
    ]


def detect_numeric_column_with_llm(df: pd.DataFrame):
    prompt = f"""
You are given column names:
{list(df.columns)}

Which ONE column is most likely purely numeric for mathematical aggregation?
Return only the exact column name.
"""

    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return r.choices[0].message["content"].strip()


def solve_csv_or_excel(file_url: str):
    r = requests.get(file_url, timeout=30)
    content = r.content

    if file_url.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
    else:
        df = pd.read_excel(BytesIO(content))

    df = df.select_dtypes(include="number")

    if df.shape[1] == 1:
        return float(df.iloc[:, 0].sum())

    # multiple numeric columns → use LLM only to choose the column
    chosen_col = detect_numeric_column_with_llm(df)
    return float(df[chosen_col].sum())


def solve_single_page(url: str):
    text = get_rendered_text(url)
    submit_url = extract_submit_url(text, url)
    files = extract_file_urls(text)

    if not files:
        raise ValueError("No data file found for computation")

    answer = solve_csv_or_excel(files[0])
    return submit_url, answer


def solve_quiz(email: str, secret: str, url: str):
    start = time.time()
    current_url = url
    last_response = None

    while current_url:
        if time.time() - start > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        submit_url, answer = solve_single_page(current_url)

        payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer
        }

        r = requests.post(submit_url, json=payload, timeout=30)
        response = r.json()
        last_response = response

        if "url" in response:
            current_url = response["url"]
        else:
            break

    return last_response
