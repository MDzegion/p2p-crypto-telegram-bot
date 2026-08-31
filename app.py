"""
app.py — Lightweight Web Health Monitor on port 7860 for Hugging Face Spaces
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="P2P Crypto Telegram Bot Status")

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "P2P Crypto Telegram Bot",
        "runtime": "24/7 Cloud Production",
        "gopay_gateway": "active (port 3005)",
        "telegram_bot": "active (polling)"
    }

@app.get("/healthz")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
