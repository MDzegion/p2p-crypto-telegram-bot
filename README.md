---
title: P2P Crypto Telegram Bot
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.20.0
app_file: app.py
pinned: false
---

# 🚀 P2P Crypto Trading Telegram Bot & GoPay Gateway

Bot Telegram P2P Crypto Exchange otomatis dengan dukungan multi-chain (EVM, Solana, TRON, TON, Sui, Aptos), integrasi pembayaran QRIS dinamis via GoPay/GoBiz Partner Gateway, verifikasi on-chain instan, dan sistem deteksi pembayaran otomatis.

---

## ✨ Fitur Utama

- **Beli Crypto (Buy Flow)**:
  - Pembayaran otomatis menggunakan QRIS Dinamis (GoPay Partner Gateway) dengan kode unik anti-bentrok.
  - Pembayaran instan menggunakan saldo internal bot (*Bot Balance*).
  - Eksekusi pengiriman koin on-chain otomatis (*Auto-Payout*) dengan notifikasi TX Hash & link Blockchain Explorer.
- **Jual Crypto (Sell Flow)**:
  - Deposit koin ke hot wallet bot dengan deteksi on-chain otomatis.
  - Opsi *Batal Jual* dan transfer bank lokal / e-Wallet manual oleh admin.
- **Tukar Antar Jaringan (OTC Convert / Cross-Chain Swap)**:
  - Konversi koin lintas rantai (contoh: SOL Solana ke USDC Base / USDT BSC) 100% full otomatis tanpa verifikasi admin.
  - Estimasi fee berjenjang (*Tiered Fee*) dan perlindungan slippage.
- **Top-Up Saldo Bot**:
  - Pengisian saldo bot via QRIS Dinamis GoPay dengan verifikasi instan.
- **Multi-RPC Failover & Resiliency**:
  - Otomatis rotasi ke RPC cadangan jika node publik mengalami *rate-limit* (HTTP 429), *timeout*, atau error 403.
- **Panel Admin Lengkap**:
  - Manajemen spread harga (`/setspread`), riwayat pesanan (`/orders`), konfirmasi manual (`/confirm`), statistik bulanan (`/stats`), broadcast (`/broadcast`), dan sinkronisasi saldo wallet hot (`/refreshwallet`).

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
│  Telegram User  │ <===> │ Python Telegram Bot    │ <===> │ SQLite Database      │
│                 │       │ (python-telegram-bot)  │       │ (WAL Mode enabled)   │
└─────────────────┘       └───────────┬────────────┘       └──────────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
              ┌─────────────────────┐   ┌──────────────────────┐
              │ GoPay Gateway (Node)│   │ Blockchain Nodes     │
              │ (Express / GoBiz)   │   │ (Web3 / Multi-RPC)   │
              └─────────────────────┘   └──────────────────────┘
```

---

## 📋 Persyaratan Sistem

- **Python**: 3.10+
- **Node.js**: 18+
- **Database**: SQLite (default) / PostgreSQL
- **PM2** (opsional untuk deployment VPS)

---

## ⚙️ Panduan Instalasi & Setup

### 1. Clone Repositori
```bash
git clone https://github.com/MDzegion/p2p-crypto-telegram-bot.git
cd p2p-crypto-telegram-bot
```

### 2. Setup Environment Variables
Salin template konfigurasi `.env.example` ke `.env`:
```bash
cp .env.example .env
```
Isi variabel lingkungan pada `.env`:
- `TELEGRAM_BOT_TOKEN`: Token bot dari [@BotFather](https://t.me/BotFather).
- `ADMIN_CHAT_IDS`: ID Telegram admin (pisahkan dengan koma).
- `EVM_PRIVATE_KEY` & `EVM_WALLET_ADDRESS`: Kredensial wallet EVM bot.
- `SOL_PRIVATE_KEY`, `TRX_PRIVATE_KEY`, `TON_PRIVATE_KEY`: Kredensial rantai non-EVM.

### 3. Install Dependensi Python
```bash
pip install -r requirements.txt
```

### 4. Install Dependensi GoPay Gateway
```bash
cd gopay-gateway
npm install
cd ..
```

---

## 🚀 Menjalankan Aplikasi

### Di Lingkungan Lokal / Windows (1-Click)
Cukup jalankan file batch:
```cmd
start_all_services.bat
```

### Di Lingkungan VPS / Linux Production (via PM2)
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## 📁 Struktur Folder

```text
├── bot/
│   ├── handlers/         # Controller alur percakapan (buy, sell, swap, balance, admin)
│   ├── keyboards/        # Layout tombol inline & menu Telegram
│   └── utils/            # Helper format pesan, validator, dan notifikasi safe
├── config/               # Settings dan asset konfigurasi
├── database/             # SQLAlchemy connection, ORM models, dan CRUD queries
├── gopay-gateway/        # Microservice Express.js untuk GoPay/GoBiz merchant
├── services/
│   ├── crypto_sender/    # Multichain sender (EVM Multi-RPC, Solana, Tron, TON)
│   ├── detector.py       # Auto-detect deposit on-chain
│   ├── gopay_service.py  # Bridge API client GoPay
│   ├── price_service.py  # Sinkronisasi harga realtime Binance
│   └── tx_verifier.py    # Verifikator transaksi blockchain
├── ecosystem.config.js   # Konfigurasi PM2 production
├── main.py               # Entrypoint bot Telegram & background scheduler
└── requirements.txt      # Dependensi Python
```

---

## 🔒 Lisensi & Keamanan

Project ini dikembangkan untuk kebutuhan operasional bot P2P crypto trading. Pastikan file `.env` dan token sesi private tidak pernah di-commit ke repositori publik.
