import time
import re
import httpx
import pandas as pd
import html as html_lib
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from llm_utils import llm_refine_answer

TIME_LIMIT = 170


async def get_rendered_page(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        html_content = await page.content()
        visible_text = await page.evaluate("() => document.body.innerText")

        await browser.close()

    return html_content, visible_text


def clean_url(u: str):
    u = html_lib.unescape(u)
    return u.strip().replace("<", "").replace(">", "")


def extract_submit_url(visible_text: str, html_str: str, base_url: str):
    text_urls = re.findall(r"https?://[^\s\"']+", visible_text)
    for u in text_urls:
        if "submit" in u.lower():
            return clean_url(u)

    html_urls = re.findall(r"https?://[^\s\"'>]+", html_str)
    for u in html_urls:
        if "submit" in u.lower():
            return clean_url(u)

    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/submit"


def extract_data_file_url(html_str: str):
    matches = re.findall(r'href="([^"]+\.(?:csv|tsv|txt|html))"', html_str, re.I)
    return matches[0] if matches else None


async def download_file(url):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        return r.text


def compute_sum_from_dataframe(df):
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "value" in df.columns:
        col = "value"
    elif "amount" in df.columns:
        col = "amount"
    else:
        numeric_cols = df.select_dtypes(include="number").columns
        col = numeric_cols[0]

    df[col] = pd.to_numeric(df[col], errors="coerce")
    return float(df[col].sum(skipna=True))


def compute_sum_from_html_table(html_str: str):
    try:
        tables = pd.read_html(html_str)
        if tables:
            return compute_sum_from_dataframe(tables[0])
    except:
        pass
    return None


async def solve_single_page(url: str):
    html_content, visible_text = await get_rendered_page(url)
    submit_url = extract_submit_url(visible_text, html_content, url)

    # 1. Try direct HTML table
    raw_answer = compute_sum_from_html_table(html_content)

    # 2. If no table, look for downloadable file
    if raw_answer is None:
        file_url = extract_data_file_url(html_content)
        if file_url:
            file_data = await download_file(file_url)
            try:
                df = pd.read_csv(pd.compat.StringIO(file_data))
                raw_answer = compute_sum_from_dataframe(df)
            except:
                raw_answer = 0.0
        else:
            raw_answer = 0.0

    try:
        final_answer = llm_refine_answer("Verify numeric table sum", raw_answer)
    except:
        final_answer = raw_answer

    return submit_url, final_answer


async def solve_quiz(email: str, secret: str, url: str):
    start = time.time()
    current_url = url
    last_response = None

    while current_url:
        if time.time() - start > TIME_LIMIT:
            return {"error": "time_limit_exceeded"}

        submit_url, answer = await solve_single_page(current_url)

        payload = {
            "email": email,
            "secret": secret,
            "url": current_url,
            "answer": answer
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(submit_url, json=payload)
                response = r.json()
        except Exception as e:
            return {"error": "submit_request_failed", "detail": str(e)}

        last_response = response

        if isinstance(response, dict) and response.get("url"):
            current_url = response["url"]
        else:
            break

    return last_response
