# ===================================================
# P2P Crypto Telegram Bot & GoPay Gateway (All-in-One)
# ===================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# 1. Install Node.js 20 & PM2
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pm2 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Space user (UID 1000)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Install Node.js dependencies
COPY gopay-gateway/package*.json ./gopay-gateway/
RUN cd gopay-gateway && npm install --production

# 4. Copy entire codebase & set permissions
COPY --chown=user:user . .
RUN chmod +x start.sh

USER user
EXPOSE 7860 3005

CMD ["./start.sh"]
