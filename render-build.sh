#!/usr/bin/env bash
set -o errexit

# Install Python packages
pip install -r requirements.txt

# Install Chromium in a way that works on Render (no system deps)
python -m playwright install chromium --browser-channel=chrome
