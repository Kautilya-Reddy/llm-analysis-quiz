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
