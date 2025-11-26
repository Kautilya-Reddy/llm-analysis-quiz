from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

SECRET = "24f2005934"

class Task(BaseModel):
    question: str
    options: list[str]
    secret: str

@app.post("/task")
def solve_task(data: Task):
    if data.secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    q = data.question.lower()

    for opt in data.options:
        if opt.lower() in q:
            return {"answer": opt}

    return {"answer": data.options[0]}
