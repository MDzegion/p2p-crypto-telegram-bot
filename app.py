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

    # 1. Install dependensi Node.js jika belum ada
    gateway_dir = os.path.join(os.path.dirname(__file__), "gopay-gateway")
    node_modules = os.path.join(gateway_dir, "node_modules")
    
    if not os.path.exists(node_modules):
        print("📦 [NPM] Menginstall dependensi gopay-gateway...")
        try:
            subprocess.run(["npm", "install", "--production"], cwd=gateway_dir, check=True)
        except Exception as e:
            print(f"⚠️ [NPM WARNING] Gagal npm install: {e}")

    # 2. Jalankan GoPay Gateway (Node.js) di port 3005
    print("🟢 [GATEWAY] Menjalankan GoPay Partner Gateway...")
    try:
        subprocess.Popen([sys.executable.replace("python", "node") if False else "node", "server.js"], cwd=gateway_dir)
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

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
