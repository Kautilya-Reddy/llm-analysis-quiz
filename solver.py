import time
import re
import base64
import httpx
import pandas as pd
import html as html_lib
from io import StringIO
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from llm_utils import llm_refine_answer
import pdfplumber
import tempfile

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


def decode_base64_script(html_str: str):
    match = re.search(r"atob\(`([^`]*)`\)", html_str)
    if not match:
        return None
    encoded = match.group(1).replace("\n", "")
    try:
        return base64.b64decode(encoded).decode()
    except Exception:
        return None


def extract_submit_url(visible_text: str, html_str: str, base_url: str):
    text_urls = re.findall(r"https?://[^\s\"']+", visible_text)
    for u in text_urls:
        if "submit" in u.lower():
            return html_lib.unescape(u).strip()

    decoded = decode_base64_script(html_str)
    if decoded:
        urls = re.findall(r"https?://[^\s\"']+", decoded)
        for u in urls:
            if "submit" in u.lower():
                return u

    parsed = urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/submit"


def extract_file_url(html_str: str, base_url: str):
    decoded = decode_base64_script(html_str)
    if decoded:
        urls = re.findall(r"https?://[^\s\"']+", decoded)
        for u in urls:
            if any(u.lower().endswith(x) for x in [".pdf", ".csv"]):
                return u

    matches = re.findall(r'href="([^"]+)"', html_str)
    for m in matches:
        if m.lower().endswith((".pdf", ".csv")):
            return urljoin(base_url, m)

    return None


async def download_file(url):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        return r.content


def compute_from_df(df: pd.DataFrame):
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "value" in df.columns:
        col = "value"
    elif "amount" in df.columns:
        col = "amount"
    else:
        numeric = df.select_dtypes(include="number").columns
        if not len(numeric):
            return 0.0
        col = numeric[0]

    df[col] = pd.to_numeric(df[col], errors="coerce")
    return float(df[col].sum(skipna=True))


def compute_from_pdf(binary_data: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(binary_data)
        tmp_path = tmp.name

    with pdfplumber.open(tmp_path) as pdf:
        if len(pdf.pages) < 2:
            return 0.0

        table = pdf.pages[1].extract_table()
        if not table or len(table) < 2:
            return 0.0

        df = pd.DataFrame(table[1:], columns=table[0])
        return compute_from_df(df)


async def solve_single_page(url: str):
    html_content, visible_text = await get_rendered_page(url)
    submit_url = extract_submit_url(visible_text, html_content, url)
    file_url = extract_file_url(html_content, url)

    raw_answer = 0.0

    if file_url:
        file_bytes = await download_file(file_url)

        if file_url.lower().endswith(".csv"):
            df = pd.read_csv(StringIO(file_bytes.decode()))
            raw_answer = compute_from_df(df)

        elif file_url.lower().endswith(".pdf"):
            raw_answer = compute_from_pdf(file_bytes)

    try:
        final_answer = llm_refine_answer("Verify numeric table sum", raw_answer)
    except Exception:
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
