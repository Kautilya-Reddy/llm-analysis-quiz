import requests
from bs4 import BeautifulSoup

def solve_quiz_task(email: str, secret: str, url: str, timeout_seconds: int = 30):
    """
    Final stable solver function.
    Accepts email, secret, url exactly as required by app.py.
    No playwright, no browser, safe for Render deployment.
    """

    print("Solver started.")
    print("Email:", email)
    print("Secret:", secret)
    print("Task URL:", url)

    # =========================
    #   1. Fetch task page
    # =========================
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return {
            "error": "failed_to_fetch_task",
            "details": str(e)
        }

    # =========================
    #   2. Extract text
    # =========================
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    # =========================
    #   3. Fake solver logic 
    #   (replace with your actual logic if needed)
    # =========================
    result_text = f"Processed task for {email}. Extracted {len(text)} characters."

    # =========================
    #   4. RETURN final result
    # =========================
    return {
        "email": email,
        "secret": secret,
        "url": url,
        "result": result_text
    }