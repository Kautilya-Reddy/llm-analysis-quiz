# llm-analysis-quiz

This repository contains the LLM Analysis Quiz solver service.
The app exposes a `/task` endpoint which accepts:
- email
- secret
- url

The solver automatically handles:
- page extraction
- decoding
- scraping
- CSV processing
- audio processing
- multi-step task flows

This version is prepared for HuggingFace Spaces deployment.
