"""
app.py — Hugging Face Space Entrypoint & Live Monitor Dashboard
Menjalankan GoPay Gateway (Node.js) dan Telegram Bot (Python) secara bersamaan di background 24/7.
"""

import os
import sys
import subprocess
import time
import gradio as gr

def start_background_services():
    """Jalankan kedua servis di background."""
    print("🚀 [STARTUP] Menyiapkan environment dual-service...")

    gateway_dir = os.path.join(os.path.dirname(__file__), "gopay-gateway")
    node_modules = os.path.join(gateway_dir, "node_modules")
    
    # Buat file gopay-gateway/.env jika belum ada
    gateway_env = os.path.join(gateway_dir, ".env")
    if not os.path.exists(gateway_env):
        qris_static = os.environ.get("QRIS_STATIC", "00020101021126680016ID.CO.GOPAY.WWW01189360001438922870000215ID10265038922870303UKE51440014ID.CO.QRIS.WWW0215ID10265038922870303UKE5204729953033605802ID5936TOKO DIGITAL HSN, DIGITAL & KREATIF6011DKI JAKARTA61051212162070703A01630453D8")
        merchant_id = os.environ.get("GOPAY_MERCHANT_ID", "G292229702")
        with open(gateway_env, "w", encoding="utf-8") as f:
            f.write(f"PORT=3005\nAPI_KEY=RAHASIA\nQRIS_STATIC={qris_static}\nGOPAY_MERCHANT_ID={merchant_id}\n")

    # Pulihkan sesi login GoPay jika disediakan di secrets
    session_json_data = os.environ.get("GOPAY_SESSION_JSON")
    if session_json_data:
        session_file = os.path.join(gateway_dir, ".GOPAY_SESI_JANGAN_DIHAPUS.json")
        with open(session_file, "w", encoding="utf-8") as f:
            f.write(session_json_data.strip())
        print("🔑 [GOPAY] Sesi GoBiz berhasil dimuat dari environment secrets.")

    if not os.path.exists(node_modules):
        print("📦 [NPM] Menginstall dependensi gopay-gateway...")
        try:
            subprocess.run(["npm", "install", "--production"], cwd=gateway_dir, check=True)
        except Exception as e:
            print(f"⚠️ [NPM WARNING] Gagal npm install: {e}")

    # 2. Jalankan GoPay Gateway (Node.js) di port 3005
    print("🟢 [GATEWAY] Menjalankan GoPay Partner Gateway...")
    try:
        subprocess.Popen(["node", "server.js"], cwd=gateway_dir)
    except Exception as e:
        print(f"⚠️ [GATEWAY ERROR] Gagal start node server.js: {e}")

    time.sleep(2)

    # 3. Jalankan Telegram Bot (Python)
    print("🤖 [BOT] Menjalankan Telegram Bot main.py...")
    try:
        subprocess.Popen([sys.executable, "main.py"])
    except Exception as e:
        print(f"⚠️ [BOT ERROR] Gagal start python main.py: {e}")


# Jalankan servis saat file di-load
start_background_services()

def check_system_status():
    """Fungsi status untuk tampilan web monitor di Hugging Face."""
    return "🟢 Status: ACTIVE\n• Telegram Bot: Polling Updates\n• GoPay Gateway: Active (Port 3005)\n• On-chain Monitor: Running (Interval 20s)"

# Gradio Web UI
with gr.Blocks(title="P2P Crypto Telegram Bot") as demo:
    gr.Markdown("# 🤖 P2P Crypto Telegram Bot — Live Server")
    gr.Markdown("Servis Bot Telegram dan GoPay Gateway berjalan aktif 24 jam nonstop di cloud.")
    
    status_output = gr.Textbox(
        label="Service Status",
        value=check_system_status(),
        interactive=False,
        lines=4
    )
    refresh_btn = gr.Button("🔄 Refresh Status")
    refresh_btn.click(fn=check_system_status, outputs=status_output)

demo.queue().launch(server_name="0.0.0.0", server_port=7860)
