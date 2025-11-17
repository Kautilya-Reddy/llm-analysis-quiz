#!/usr/bin/env bash
set -o errexit

# Install Python packages
pip install -r requirements.txt

# Install Chromium browser without system dependency checks
python -m playwright install chromium
python -m playwright install-deps chromium || true
