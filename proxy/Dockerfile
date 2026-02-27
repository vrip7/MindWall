# MindWall — IMAP/SMTP Proxy Dockerfile
# Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose IMAP and SMTP proxy ports
EXPOSE 1143 1025

# Run the proxy
CMD ["python", "main.py"]
