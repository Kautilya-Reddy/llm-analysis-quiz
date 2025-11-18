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

This repository contains the LLM Analysis Quiz solver service.

The app exposes a `/task` endpoint which accepts:
- `email`
- `secret`
- `url`

The solver automatically handles:
- page extraction
- decoding
- scraping
- CSV processing
- audio processing
- multi-step quiz workflows

This version is prepared for deployment on **HuggingFace Spaces (Docker)**.
