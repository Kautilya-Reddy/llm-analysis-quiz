import time
import re
import base64
import httpx
import pandas as pd
from io import StringIO
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import pdfplumber
import tempfile

TIME_LIMIT = 170


# ---------- Browser (single instance) ----------
async def fetch_page(browser, url: str):
    page = await browser.new_page()
    await page.goto(url, timeout=60000)
    await page.wait_for_load_state("networkidle")
    html = await page.content()
    text = await page.evaluate("() => document.body.innerText")
    await page.close()
    return html, text


def decode_base64(html: str):
    m = re.search(r"atob\(`([^`]*)`\)", html)
    if not m:
        return None
    try:
        return base64.b64decode(m.group(1).replace("\n", "")).decode()
    except Exception:
        return None


def extract_submit_url(html: str, text: str):
    urls = re.findall(r"https?://[^\s\"']+", text)
    for u in urls:
        if "submit" in u.lower():
            return u

    decoded = decode_base64(html)
    if decoded:
        urls = re.findall(r"https?://[^\s\"']+", decoded)
        for u in urls:
            if "submit" in u.lower():
                return u

    return None   # ❗ NO FALLBACK (spec-compliant)


def extract_file_url(html: str, base: str):
    decoded = decode_base64(html)
    if decoded:
        urls = re.findall(r"https?://[^\s\"']+", decoded)
        for u in urls:
            if u.lower().endswith((".csv", ".pdf")):
                return u

    matches = re.findall(r'href="([^"]+)"', html)
    for m in matches:
        if m.lower().endswith((".csv", ".pdf")):
            return urljoin(base, m)

    return None


def compute_from_df(df: pd.DataFrame):
    df.columns = [c.strip().lower() for c in df.columns]
    num = df.select_dtypes(include="number")
    if num.empty:
        return 0.0
    return float(num.iloc[:, 0].sum(skipna=True))


def compute_from_pdf(binary: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(binary)
        path = f.name

    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) < 2:
            return 0.0
        table = pdf.pages[1].extract_table()
        if not table:
            return 0.0
        df = pd.DataFrame(table[1:], columns=table[0])
        return compute_from_df(df)


async def solve_quiz(email: str, secret: str, url: str):
    start = time.time()
    current = url
    last = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        while current:
            if time.time() - start > TIME_LIMIT:
                return {"error": "time_limit_exceeded"}

            html, text = await fetch_page(browser, current)
            submit_url = extract_submit_url(html, text)

            if not submit_url:
                return {"error": "submit_url_not_found"}

            answer = 0.0
            file_url = extract_file_url(html, current)

            if file_url:
                async with httpx.AsyncClient(timeout=30) as client:
                    data = await client.get(file_url)
                if file_url.endswith(".csv"):
                    df = pd.read_csv(StringIO(data.text))
                    answer = compute_from_df(df)
                elif file_url.endswith(".pdf"):
                    answer = compute_from_pdf(data.content)

            payload = {
                "email": email,
                "secret": secret,
                "url": current,
                "answer": answer
            }

            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(submit_url, json=payload)
                resp = r.json()

            last = resp
            current = resp.get("url")

        await browser.close()
    return last
