from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from solver import solve_quiz
import json

app = FastAPI()
import os
SECRET = os.environ.get("SECRET", "24f2005934")

@app.post("/task")
async def run_task(request: Request):
    # --- 1. Raw JSON handling (required for HTTP 400) ---
    try:
        body = await request.body()
        data = json.loads(body)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"}
        )

    # --- 2. Required fields check ---
    required = {"email", "secret", "url"}
    if not required.issubset(data):
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required fields"}
        )

    # --- 3. Secret validation ---
    if data["secret"] != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # --- 4. Run solver safely ---
    try:
        result = await solve_quiz(
            email=data["email"],
            secret=data["secret"],
            url=data["url"]
        )
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal error", "detail": str(e)}
        )
