# ============================
# P2P Crypto Trading Bot
# ============================
# Runs the Telegram bot (long-polling) via main.py.

FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr (useful for Docker logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Entry point — runs bot polling
CMD ["python", "main.py"]
