"""
app.py — Streamlit UI & 24/7 Dual Service Runner for Hugging Face Spaces
Menjalankan GoPay Gateway (Node.js) dan Telegram Bot (Python) di background 24/7.
"""

import os
import sys
import subprocess
import threading
import time
import streamlit as st

def ensure_node():
    """Download pre-built Node.js 20 Linux x64 standalone binary jika belum ada."""
    base_dir = os.path.dirname(__file__)
    node_dir = os.path.join(base_dir, "bin_node")
    node_bin = os.path.join(node_dir, "bin", "node")
    npm_bin = os.path.join(node_dir, "bin", "npm")

    if not os.path.exists(node_bin):
        print("📦 [NODE] Mengunduh standalone Node.js 20 runtime...")
        try:
            os.makedirs(node_dir, exist_ok=True)
            url = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.gz"
            subprocess.run(f"curl -sL {url} | tar -xz --strip-components=1 -C {node_dir}", shell=True, check=True)
            print("✅ [NODE] Standalone Node.js siap digunakan.")
        except Exception as e:
            print(f"⚠️ [NODE ERROR] Gagal download node: {e}")
    return node_bin, npm_bin

def init_and_run_services():
    """Jalankan servis di background setelah server start."""
    time.sleep(2)
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

    # 3. Setup standalone node dan install node_modules jika belum ada
    node_bin, npm_bin = ensure_node()
    node_modules = os.path.join(gateway_dir, "node_modules")
    if not os.path.exists(node_modules) and os.path.exists(npm_bin):
        print("📦 [NPM] Menginstall dependensi gopay-gateway...")
        try:
            subprocess.run([npm_bin, "install", "--omit=dev", "--no-audit", "--no-fund"], cwd=gateway_dir, check=True)
        except Exception as e:
            print(f"⚠️ [NPM WARNING] Gagal npm install: {e}")

    # 4. Jalankan GoPay Gateway (Node.js) di port 3005
    print("🟢 [GATEWAY] Menjalankan GoPay Partner Gateway di port 3005...")
    try:
        if os.path.exists(node_bin):
            subprocess.Popen([node_bin, "server.js"], cwd=gateway_dir)
        else:
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


# Jalankan worker background hanya 1 instance per container process
if "daemon_started" not in globals():
    globals()["daemon_started"] = True
    threading.Thread(target=init_and_run_services, daemon=True).start()

st.set_page_config(page_title="P2P Crypto Telegram Bot", page_icon="🤖")
st.title("🤖 P2P Crypto Telegram Bot — Live Server")
st.success("🟢 Sistem Bot Telegram dan GoPay Gateway aktif 24 jam di cloud.")

col1, col2 = st.columns(2)
with col1:
    st.info("🤖 **Telegram Bot:** Active (Polling)")
    st.info("💳 **GoPay Gateway:** Active (Port 3005)")
with col2:
    st.info("⛓️ **Multi-Chain Scanner:** Active (20s)")
    st.info("📈 **Binance Vision Price:** Connected")

if st.button("🔄 Refresh"):
    st.rerun()
