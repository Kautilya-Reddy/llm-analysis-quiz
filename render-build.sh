#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Install Playwright Chromium browser
python -m playwright install chromium
