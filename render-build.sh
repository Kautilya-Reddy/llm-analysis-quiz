#!/usr/bin/env bash
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Install Chromium dependencies manually
apt-get update
apt-get install -y \
  libnss3 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libcups2 \
  libdrm2 \
  libdbus-1-3 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2 \
  libatspi2.0-0 \
  libx11-xcb1

# Install Chromium browser
python -m playwright install chromium
