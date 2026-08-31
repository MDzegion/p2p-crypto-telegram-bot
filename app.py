"""
app.py — Minimal Gradio + Telegram Bot Runner for Hugging Face Spaces
"""
import os
import sys
import subprocess
import threading
import time
import gradio as gr

def start_bot():
    time.sleep(2)
    print("🚀 [STARTUP] Menjalankan main.py Telegram Bot...")
    subprocess.Popen([sys.executable, "main.py"])

threading.Thread(target=start_bot, daemon=True).start()

def get_status():
    return "🟢 Bot Telegram P2P Crypto Aktif 24/7"

demo = gr.Blocks()
with demo:
    gr.Markdown("# 🤖 P2P Crypto Telegram Bot")
    status = gr.Textbox(value=get_status, label="Status")
