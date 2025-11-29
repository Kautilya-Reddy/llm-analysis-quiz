import time
import re
import requests
import pandas as pd
import html as html_lib
import base64
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

TIME_LIMIT = 170


def get_rendered_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        html_content = page.content()
        visible_text = page.evaluate("() => document.body.innerText")

        browser.close()

    return html_content, visible_text


def clean_url(u: str):
    u = html_lib.unescape(u)
    u = u.strip().replace("<", "").replace(">", "")
    return u


def extract_submit_url(visible_text: str, html_str: str, base_url: str):
    text_urls = re.findall(r"https?://[^\s\"']+", visible_text)
    for u in text_urls:
        if "submit" in u.lower():
            return clean_url(u)

    html_urls = re.findall(r"https?://[^\s\"'>]+", html_str)
    for u in html_urls:
        u = clean_url(u)
        if "submit" in u.lower():
            return u

    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/submit"


# ---------- SOLVERS ----------

def solve_api_sum_task(text: str):
    api_match = re.search(r"https?://[^\s\"']+/api/[^\s\"']+", text)
    if not api_match:
        return None

    api_url = api_match.group(0)
    params = dict(re.findall(r"(email|secret)=([^&\s]+)", api_url))
    r = requests.get(api_url, params=params, timeout=30)
    data = r.json()
    return float(sum(data.get("values", [])))


def solve_hidden_dom_task(html_str: str):
    match = re.search(r'class="hidden-key".*?>(.*?)<', html_str, re.DOTALL)
    if not match:
        return None

    reversed_text = match.group(1).strip()
    return reversed_text[::-1]


def solve_html_table_sum(html_str: str):
    try:
        tables = pd.read_html(html_str)
    except Exception:
        return None

    if not tables:
        return None

    df = tables[0]
    df = df.apply(pd.to_numeric, errors="coerce")

    if "value" in df.columns:
        return float(df["value"].sum(skipna=True))

    numeric_cols = df.select_dtypes(include="number").columns
    if not len(numeric_cols):
        return None

    return float(df[numeric_cols[0]].sum(skipna=True))


def solve_file_csv_sum(text: str):
    file_match = re.search(r"https?://[^\s\"']+\.csv", text)
    if not file_match:
        return None

    file_url = file_match.group(0)
    df = pd.read_csv(file_url)
    return float(df.select_dtypes(include="number").sum().sum())


def solve_generic(text: str, html: str):
    answer = solve_api_sum_task(text)
    if answer is not None:
        return answer

    answer = solve_hidden_dom_task(html)
    if answer is not None:
        return answer

    answer = solve_html_table_sum(html)
    if answer is not None:
        return answer

    answer = solve_file_csv_sum(text)
    if answer is not None:
        return answer

    return None


def safe_json_response(resp):
    try:
        return resp.json()
    except Exception:
        return {
            "raw_text": resp.text[:500],
            "status_code": resp.status_code
        }


def solve_single_page(url: str):
    html_content, visible_text = get_rendered_page(url)
    submit_url = extract_submit_url(visible_text, html_content, url)

    answer = solve_generic(visible_text, html_content)

    if answer is None:
        answer = 0   # safe fallback (doc allows wrong → retry)

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

        try:
            r = requests.post(submit_url, json=payload, timeout=30)
            response = safe_json_response(r)
        except Exception as e:
            return {
                "error": "submit_request_failed",
                "detail": str(e)
            }

        last_response = response

        if isinstance(response, dict) and "url" in response and response["url"]:
            current_url = response["url"]
        else:
            break

    return last_response
