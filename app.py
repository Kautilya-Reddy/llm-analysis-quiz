from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from solver import solve_quiz

app = FastAPI()

SECRET = "24f2005934"

class QuizTask(BaseModel):
    email: str
    secret: str
    url: str

@app.post("/task")
async def run_task(task: QuizTask = Body(...)):
    if task.secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    result = await solve_quiz(
        email=task.email,
        secret=task.secret,
        url=task.url
    )

    return result
