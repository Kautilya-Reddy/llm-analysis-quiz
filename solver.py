import time, json, requests
from playwright.sync_api import sync_playwright


def call_llm_generic(llm_api, llm_key, system_prompt, user_prompt, context_text, timeout=30):
    headers = {"Content-Type": "application/json"}
    if llm_key:
        headers["Authorization"] = f"Bearer {llm_key}"

    body = {
        "system": system_prompt,
        "user": user_prompt + "\n\nCONTEXT:\n" + context_text,
        "max_tokens": 1200
    }

    r = requests.post(llm_api, json=body, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def render_url_text(url, timeout=30):
    with sync_playwright() as p:
        chromium_path = p.chromium.executable_path

        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_path,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--disable-setuid-sandbox",
                "--disable-dev-tools",
                "--no-zygote"
            ]
        )

        page = browser.new_page()
        page.set_default_navigation_timeout(int(timeout * 1000))
        page.goto(url)
        time.sleep(1.0)

        text = page.evaluate("() => document.documentElement.innerText")
        html = page.content()

        browser.close()

    return text, html


def extract_json_from_response(resp):
    if isinstance(resp, dict) and "text" in resp:
        candidate = resp["text"]
    else:
        candidate = str(resp)

    candidate = candidate.strip()

    try:
        return json.loads(candidate)
    except:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(candidate[start:end + 1])
            except:
                pass
    return None


def solve_quiz_task(email, secret, url, llm_api, llm_key, timeout_seconds=170):
    t0 = time.time()

    page_text, page_html = render_url_text(
        url,
        timeout=min(30, timeout_seconds - 10)
    )

    system_prompt = "You are precise. Return ONLY JSON with keys answer, submit_url, submit_payload."
    user_prompt = "Return JSON: {\"answer\":...,\"submit_url\":\"...\",\"submit_payload\":{...}}"

    llm_resp = call_llm_generic(
        llm_api=llm_api,
        llm_key=llm_key,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        context_text=page_text,
        timeout=min(60, timeout_seconds - (time.time() - t0))
    )

    parsed = extract_json_from_response(llm_resp)
    if not parsed:
        raise RuntimeError("LLM returned no parseable JSON")

    answer = parsed.get("answer")
    submit_url = parsed.get("submit_url") or parsed.get("submitUrl")
    submit_payload = parsed.get("submit_payload") or parsed.get("submitPayload") or {}

    if not submit_url:
        for token in page_html.split():
            if "https://" in token and "submit" in token:
                submit_url = token.strip('",')
                break

    if not submit_url:
        raise RuntimeError("No submit_url found")

    final_payload = {"email": email, "secret": secret, "url": url}
    final_payload.update(submit_payload)
    final_payload["answer"] = answer

    r = requests.post(submit_url, json=final_payload, timeout=30)
    r.raise_for_status()

    return {
        "status": "submitted",
        "submit_response": r.json(),
        "llm_parsed": parsed
    }
