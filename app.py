import os
from flask import Flask, request, jsonify
from solver import solve_quiz_task

app = Flask(__name__)

MAX_TOTAL_SECONDS = 170  # stay under 3 minutes total
EXPECTED_SECRET = os.environ.get("EXPECTED_SECRET")


@app.route("/", methods=["GET"])
def home():
    return "OK", 200


@app.route("/task", methods=["POST"])
def task():
    # 1. Parse JSON safely
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid_json"}), 400

    email = data.get("email")
    secret = data.get("secret")
    url = data.get("url")

    # 2. Required fields check
    if not email or not secret or not url:
        return jsonify({"error": "missing_required_fields"}), 400

    # 3. Secret check (only if EXPECTED_SECRET is set)
    if EXPECTED_SECRET is not None and secret != EXPECTED_SECRET:
        return jsonify({"error": "forbidden"}), 403

    # 4. Call solver
    result = solve_quiz_task(
        email=email,
        secret=secret,
        url=url,
        timeout_seconds=MAX_TOTAL_SECONDS,
    )

    # 5. Always return JSON
    return jsonify(result), 200


if __name__ == "__main__":
    # Not used on HF, but fine locally
    app.run(host="0.0.0.0", port=10000)
