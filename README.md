---
title: LLM Analysis Quiz
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
sdk_version: "20.10.12"
app_file: app.py
pinned: false
---

# LLM Analysis Quiz – Automated Quiz Solver

This project implements an automated quiz-solving engine for the **TDS Project 2 – LLM Analysis Quiz**.

The system exposes a POST API endpoint that receives quiz tasks, dynamically solves data-related questions, and submits answers back to the provided quiz endpoints within strict time limits.

---

## Architecture Overview

1. **FastAPI**  
   - Provides the `/task` POST endpoint.
   - Implements strict API contract handling:
     - Invalid JSON → HTTP 400
     - Invalid secret → HTTP 403
     - Valid requests → HTTP 200

2. **Playwright (Headless Chromium)**  
   - Used to render JavaScript-driven quiz pages.
   - Extracts visible content and embedded base64 instructions.
   - Supports multi-step quiz navigation.

3. **Data Processing (Pandas + PDFPlumber)**  
   - CSV files are parsed and aggregated using Pandas.
   - PDF tables are extracted using PDFPlumber.
   - Numeric aggregation (sum) is computed deterministically.

4. **Dynamic URL Chaining**  
   - Submit URLs are extracted dynamically from page content.
   - No URLs are hardcoded.
   - Supports chained quizzes until completion.

5. **Deterministic Execution**  
   - No external LLM APIs are used during evaluation.
   - Ensures reproducible and reliable behavior without API keys.

---

## API Usage

### Endpoint
POST /task

### Request Body
```json
{
  "email": "student_email@domain",
  "secret": "your_secret",
  "url": "quiz_task_url"
}
```