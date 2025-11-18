import re
import time
import json
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


def debug(label, text):
    print(f"\n===== {label} =====")
    try:
        print(text[:3000])
    except:
        print(text)
    print("\n====================\n")


def extract_base64_strings(html):
    return re.findall(r'atob\([\'"]([^\'"]+)[\'"]\)', html, flags=re.DOTALL)


def decode_b64(s):
    try:
        return base64.b64decode(s).decode("utf-8", errors="replace")
    except:
        return None


def solve_quiz_task(email, secret, url, timeout_seconds=180):
    start = time.time()
    results = {"email": email, "url_chain": [], "attempts": []}
    current = url

    print("\n🔥 SOLVER STARTED 🔥")
    print("Starting URL:", url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            while True:
                if time.time() - start > timeout_seconds:
                    return {"error": "timeout", "results": results}

                page = browser.new_page()
                page.goto(current, wait_until="networkidle", timeout=30000)

                html = page.content()
                text = page.inner_text("body") if page.query_selector("body") else ""
                results["url_chain"].append(current)

                debug("RAW HTML", html)
                debug("PAGE TEXT", text)

                # -----------------------------------------
                # 1) Find submit URL (JS-created or raw)
                # -----------------------------------------
                submit_links = page.eval_on_selector_all(
                    "a[href*='submit']", "els => els.map(e => e.getAttribute('href'))"
                )
                if submit_links:
                    submit_url = urljoin(current, submit_links[0])
                else:
                    m = re.search(r"https?://[^\s'\"<>]+/submit[^\s'\"<>]*", html + text)
                    submit_url = m.group(0) if m else None

                debug("SUBMIT URL", submit_url or "None")

                # -----------------------------------------
                # 2) Look for SCRAPE tasks
                # -----------------------------------------
                scrape_match = re.search(r"Scrape\s+([^\s<]+)", text)
                if scrape_match:
                    scrape_rel = scrape_match.group(1)
                    scrape_url = urljoin(current, scrape_rel)
                    debug("SCRAPE URL", scrape_url)

                    # Fetch scrape page
                    try:
                        r = requests.get(scrape_url, timeout=10)
                        r.raise_for_status()
                        scrape_html = r.text
                        debug("SCRAPE PAGE HTML", scrape_html)
                    except Exception as e:
                        return {"error": "scrape_failed", "details": str(e)}

                    # Extract secret code from scrape page or JS file
                    # Case 1: Secret written plainly
                    m = re.search(r"([A-Za-z0-9]{5,})", scrape_html)
                    answer = None
                    if m:
                        answer = m.group(1)

                    # Case 2: page uses <script src="demo-scrape.js">
                    scripts = re.findall(r'src="([^"]+)"', scrape_html)
                    for src in scripts:
                        if "demo-scrape" in src:
                            js_url = urljoin(scrape_url, src)
                            debug("SCRAPE JS URL", js_url)
                            try:
                                js = requests.get(js_url, timeout=10).text
                                debug("SCRAPE JS CONTENT", js)
                                tokens = re.findall(r"[A-Za-z0-9]+", js)
                                if tokens:
                                    answer = tokens[-1]      # secret is last token
                            except:
                                pass

                    if not answer:
                        answer = "NA"  # fallback

                    debug("SCRAPE ANSWER", answer)

                # -----------------------------------------
                # 3) AUDIO / CSV tasks
                # -----------------------------------------
                elif "CSV file" in text or ".csv" in html:

                    # find csv link
                    csv_links = page.eval_on_selector_all(
                        "a[href*='.csv']", "els => els.map(e => e.href)"
                    )
                    if csv_links:
                        csv_url = csv_links[0]
                        debug("CSV URL", csv_url)

                        csv_text = requests.get(csv_url, timeout=10).text
                        nums = re.findall(r"[-+]?\d*\.\d+|\d+", csv_text)
                        nums = list(map(float, nums))

                        # cutoff
                        cutoff_el = page.query_selector("#cutoff")
                        cutoff = int(cutoff_el.inner_text().strip()) if cutoff_el else 0
                        debug("CUTOFF", cutoff)

                        # example rule: sum numbers greater than cutoff
                        answer = sum(n for n in nums if n > cutoff)
                        debug("CSV ANSWER", str(answer))

                    else:
                        answer = "NA"

                # -----------------------------------------
                # 4) Base64 encoded tasks
                # -----------------------------------------
                else:
                    b64_strings = extract_base64_strings(html)
                    decoded = [decode_b64(x) for x in b64_strings if decode_b64(x)]
                    if decoded:
                        debug("DECODED BASE64", "\n----\n".join(decoded))
                        # try simple numeric extraction
                        m = re.search(r"(\d+)", "\n".join(decoded))
                        answer = int(m.group(1)) if m else "NA"
                    else:
                        # fallback numeric extraction
                        m = re.search(r"(\d+)", text)
                        answer = int(m.group(1)) if m else "NA"

                # -----------------------------------------
                # 5) SEND ANSWER
                # -----------------------------------------
                if not submit_url:
                    return {"error": "submit_not_found", "page": current, "results": results}

                payload = {
                    "email": email,
                    "secret": secret,
                    "url": current,
                    "answer": answer
                }

                debug("PAYLOAD", json.dumps(payload, indent=2))

                try:
                    resp = requests.post(submit_url, json=payload, timeout=15)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    return {"error": "submit_failed", "details": str(e), "payload": payload}

                debug("SERVER RESPONSE", json.dumps(data, indent=2))

                results["attempts"].append({"payload": payload, "response": data})

                next_url = data.get("url")
                if not next_url:
                    return {"status": "finished", "results": results}

                current = next_url

        finally:
            browser.close()
