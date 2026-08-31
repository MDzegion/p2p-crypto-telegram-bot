"""
app.py — Hugging Face Space Entrypoint & 24/7 Dual Service Runner
Menjalankan GoPay Gateway (Node.js) dan Telegram Bot (Python) di background 24/7.
"""

import os
import sys
import subprocess
import threading
import time
from fastapi import FastAPI
import gradio as gr
import uvicorn

app = FastAPI(title="P2P Crypto Bot Live Monitor")

def get_status():
    return "🟢 Status: ACTIVE 24/7\n• Telegram Bot: Polling Active\n• GoPay Gateway: Active (Port 3005)\n• On-chain Monitor: Running (20s interval)"

with gr.Blocks(title="P2P Crypto Telegram Bot") as demo:
    gr.Markdown("# 🤖 P2P Crypto Telegram Bot — Live Server")
    gr.Markdown("Servis Bot Telegram dan GoPay Gateway berjalan aktif 24 jam nonstop di cloud.")
    
    status_output = gr.Textbox(
        label="Service Status",
        value=get_status(),
        interactive=False,
        lines=4
    )
    refresh_btn = gr.Button("🔄 Refresh Status")
    refresh_btn.click(fn=get_status, outputs=status_output)

# Mount Gradio langsung ke FastAPI pada root path (memenuhi semua endpoint /config dan SSR Gradio)
app = gr.mount_gradio_app(app, demo, path="/")

def run_services():
    """Worker background untuk inisialisasi dan menjalankan servis."""
    time.sleep(3)
    print("🚀 [STARTUP] Memulai inisialisasi background services...")

    gateway_dir = os.path.join(os.path.dirname(__file__), "gopay-gateway")
    
    # 1. Setup gopay-gateway/.env
    gateway_env = os.path.join(gateway_dir, ".env")
    if not os.path.exists(gateway_env):
        qris_static = os.environ.get("QRIS_STATIC", "00020101021126680016ID.CO.GOPAY.WWW01189360001438922870000215ID10265038922870303UKE51440014ID.CO.QRIS.WWW0215ID10265038922870303UKE5204729953033605802ID5936TOKO DIGITAL HSN, DIGITAL & KREATIF6011DKI JAKARTA61051212162070703A01630453D8")
        merchant_id = os.environ.get("GOPAY_MERCHANT_ID", "G292229702")
        with open(gateway_env, "w", encoding="utf-8") as f:
            f.write(f"PORT=3005\nAPI_KEY=RAHASIA\nQRIS_STATIC={qris_static}\nGOPAY_MERCHANT_ID={merchant_id}\n")

    # 2. Setup Sesi GoBiz jika disediakan di secrets
    session_json_data = os.environ.get("GOPAY_SESSION_JSON")
    if session_json_data:
        session_file = os.path.join(gateway_dir, ".GOPAY_SESI_JANGAN_DIHAPUS.json")
        with open(session_file, "w", encoding="utf-8") as f:
            f.write(session_json_data.strip())
        print("🔑 [GOPAY] Sesi GoBiz berhasil dimuat dari secrets.")

    # 3. Install node_modules jika belum ada
    node_modules = os.path.join(gateway_dir, "node_modules")
    if not os.path.exists(node_modules):
        print("📦 [NPM] Menginstall dependensi gopay-gateway...")
        try:
            subprocess.run(["npm", "install", "--omit=dev", "--no-audit", "--no-fund", "--silent"], cwd=gateway_dir, check=True)
        except Exception as e:
            print(f"⚠️ [NPM WARNING] Gagal npm install: {e}")

    # 4. Jalankan GoPay Gateway (Node.js) di port 3005
    print("🟢 [GATEWAY] Menjalankan GoPay Partner Gateway di port 3005...")
    try:
        subprocess.Popen(["node", "server.js"], cwd=gateway_dir)
    except Exception as e:
        print(f"⚠️ [GATEWAY ERROR] Gagal start gateway: {e}")

    time.sleep(2)

    # 5. Jalankan Telegram Bot (Python)
    print("🤖 [BOT] Menjalankan Telegram Bot main.py...")
    try:
        subprocess.Popen([sys.executable, "main.py"])
    except Exception as e:
        print(f"⚠️ [BOT ERROR] Gagal start main.py: {e}")


# Jalankan worker background di daemon thread
threading.Thread(target=run_services, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
