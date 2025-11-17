from flask import Flask, request, jsonify
from solver import solve_quiz_task

app = Flask(__name__)

MAX_TOTAL_SECONDS = 30


@app.route("/", methods=["GET"])
def home():
    return "OK", 200


@app.route("/task", methods=["POST"])
def task():
    data = request.get_json(force=True)

    # Extract required fields
    email = data.get("email")
    secret = data.get("secret")
    url = data.get("url")

    if not email or not secret or not url:
        return jsonify({"error": "missing_required_fields"}), 400

    # Call solver
    result = solve_quiz_task(
        email=email,
        secret=secret,
        url=url,
        timeout_seconds=MAX_TOTAL_SECONDS
    )

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
