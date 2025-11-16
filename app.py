from flask import Flask, request, jsonify
import os
from keepalive import start_keepalive_thread
from solver import solve_quiz_task

app = Flask(__name__)

SOLVER_LLM_API = os.environ.get("SOLVER_LLM_API", "")
SOLVER_LLM_KEY = os.environ.get("SOLVER_LLM_KEY", "")
EXPORTED_SECRET = os.environ.get("EXPORTED_SECRET", "")
MAX_TOTAL_SECONDS = int(os.environ.get("MAX_TOTAL_SECONDS", "180"))

@app.route("/", methods=["GET"])
def index():
    return jsonify({"ok": True}), 200

@app.route("/task", methods=["POST"])
def task():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid JSON"}), 400

    email = payload.get("email")
    secret = payload.get("secret")
    url = payload.get("url")

    if not (email and secret and url):
        return jsonify({"error": "missing_fields"}), 400

    if EXPORTED_SECRET and secret != EXPORTED_SECRET:
        return jsonify({"error": "invalid_secret"}), 403

    result = solve_quiz_task(
        email=email,
        secret=secret,
        url=url,
        llm_api=SOLVER_LLM_API,
        llm_key=SOLVER_LLM_KEY,
        timeout_seconds=MAX_TOTAL_SECONDS
    )
    return jsonify(result), 200

if __name__ == "__main__":
    start_keepalive_thread()
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
