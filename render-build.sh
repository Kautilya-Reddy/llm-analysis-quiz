#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# DO NOT install browsers here (Render blocks it)
# python -m playwright install chromium
# python -m playwright install-deps chromium
