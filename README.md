This project implements a hybrid automated quiz-solving engine.

Architecture:
1. Playwright is used for JavaScript-rendered page scraping.
2. Pandas performs numerical data extraction and aggregation.
3. A lightweight LLM verification layer is used to validate computed answers.
4. Matplotlib is used to generate base64-encoded visualizations when required.
5. Dynamic URL chaining allows multi-step quiz solving.

Prompt-injection testing is evaluated externally using the submitted system and user prompts.
