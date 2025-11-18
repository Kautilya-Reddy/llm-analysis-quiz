import os
from flask import Flask, request, jsonify
from solver import solve_quiz_task

app = Flask(__name__)

MAX_TOTAL_SECONDS = int(os.environ.get("MAX_TOTAL_SECONDS", "180"))
EXPECTED_SECRET = os.environ.get("EXPECTED_SECRET", "")

@app.route("/", methods=["GET"])
def home():
    return "OK", 200

@app.route("/task", methods=["POST"])
def task():
    data = request.get_json(force=True)
    email = data.get("email")
    secret = data.get("secret")
    url = data.get("url")

    if not email or not secret or not url:
        return jsonify({"error": "missing_required_fields"}), 400

    if EXPECTED_SECRET and secret != EXPECTED_SECRET:
        return jsonify({"error": "invalid_secret"}), 403

    result = solve_quiz_task(
        email=email,
        secret=secret,
        url=url,
        timeout_seconds=MAX_TOTAL_SECONDS
    )
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
