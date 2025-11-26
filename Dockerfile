FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libgtk-3-0 libdrm2 libgbm1 \
    libasound2 libxshmfence1 libxrandr2 libxcomposite1 \
    libxdamage1 libxfixes3 libxkbcommon0 libpango-1.0-0 \
    libcairo2 libx11-xcb1 libx11-6 libxcb1 libdbus-1-3 \
    curl wget unzip && \
    apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install chromium

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
