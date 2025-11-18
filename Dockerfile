# Use a slim Python image for lightweight and fast boot
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (curl is used by some tasks)
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean

# Copy application files
COPY requirements.txt .
COPY app.py .
COPY solver.py .
COPY README.md .
COPY LICENSE .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose required port for HuggingFace Spaces
EXPOSE 7860

# Start FastAPI app on Space launch
CMD ["python", "app.py"]
