import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_refine_answer(question: str, raw_answer):
    prompt = f"""
You are a strict verification assistant.
Question: {question}
Computed answer: {raw_answer}
Return only the final verified answer without explanation.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )

    return response.choices[0].message.content.strip()
