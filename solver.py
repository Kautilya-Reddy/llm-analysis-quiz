def render_url_text(url, timeout=30):
    import playwright
    from playwright.sync_api import sync_playwright
    import subprocess, os, time

    # Ensure browser is installed at runtime
    chromium_path = "/opt/render/.cache/ms-playwright/chromium-1194/chrome-linux/chrome"
    if not os.path.exists(chromium_path):
        subprocess.run(
            ["python3", "-m", "playwright", "install", "chromium"],
            check=True
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
            ]
        )

        page = browser.new_page()
        page.set_default_navigation_timeout(timeout * 1000)
        page.goto(url)

        time.sleep(1)
        text = page.evaluate("() => document.documentElement.innerText")
        html = page.content()

        browser.close()

    return text, html
