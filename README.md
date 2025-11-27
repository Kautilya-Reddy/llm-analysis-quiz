---
title: LLM Analysis Quiz Solver
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_file: app.py
pinned: false
---

# LLM Analysis Quiz Solver

This service implements a robust solver for the **TDS LLM Analysis Quiz**.

## Features
- Accepts quiz tasks via a FastAPI `/task` endpoint
- Secure secret validation
- JavaScript-rendered page handling using **Playwright**
- Automatic extraction of submit URLs from visible page text
- Deterministic numeric computation using **pandas**
- Robust handling of:
  - Invalid JSON responses
  - Missing tables
  - Network & DNS failures
  - 404 submit endpoints
- Fully compatible with HuggingFace Spaces (Docker)

## API Contract

POST `/task`

```json
{
  "email": "your email",
  "secret": "your secret",
  "url": "quiz url"
}
