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

This project implements an automated quiz-solving engine for TDS Project 2 – LLM Analysis Quiz. The system exposes a POST API endpoint that receives quiz tasks, solves data-related questions involving data sourcing, preparation, analysis, and visualization, and submits answers back to the provided quiz endpoints within strict time limits.

## Architecture Overview

1. FastAPI  
Provides the /task POST endpoint, verifies request validity and secret correctness, and enforces strict API behavior: invalid JSON returns HTTP 400, invalid secret returns HTTP 403, and valid requests return HTTP 200.

2. Playwright (Headless Chromium)  
Renders JavaScript-driven quiz pages that require DOM execution, extracts visible text and embedded base64 instructions, and supports multi-step quiz navigation through chained URLs.

3. Data Sourcing and Preparation  
Downloads external resources referenced by the quiz such as CSV, PDF, and image files, cleans and normalizes tabular data, and extracts structured tables from PDFs including page-specific tables.

4. Data Analysis  
Performs deterministic computations such as filtering and aggregation. Numeric aggregation (for example, summation) is implemented using Pandas to ensure correctness and speed under time constraints.

5. Visualization and Flexible Answer Handling  
The solver dynamically adapts the answer format and can return numbers, booleans, strings, base64-encoded files (such as images or visualizations), or structured JSON objects depending on quiz requirements.

6. Dynamic URL Chaining  
Submit URLs are extracted dynamically from quiz content without hardcoding. The solver supports retrying incorrect submissions and automatically follows new quiz URLs until completion.

7. Deterministic Execution Strategy  
The core quiz-solving logic is deterministic and rule-based. No external LLM APIs are required during evaluation, avoiding hallucinations, reducing latency, and ensuring reproducibility within the allowed time window.

## API Usage

Endpoint: POST /task

Request Body:
```json
{
  "email": "student_email@domain",
  "secret": "your_secret",
  "url": "quiz_task_url"
}
```