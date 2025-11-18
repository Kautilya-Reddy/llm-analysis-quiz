FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Playwright (required for Chromium)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    libnss3 \
    libasound2 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libxfixes3 \
    libgtk-3-0 \
    libx11-xcb1 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries
RUN python -m playwright install --with-deps chromium

COPY . /app

EXPOSE 7860

# Start the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
