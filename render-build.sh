#!/usr/bin/env bash
set -o errexit

# Install Python packages
pip install -r requirements.txt

# Install Chromium browser (this actually downloads the browser binary)
python -m playwright install chromium

# Try to install deps but ignore failure (Render cannot install system deps)
python -m playwright install-deps chromium || true
