#!/bin/bash
set -e

echo "🚀 [STARTUP] Menyiapkan environment dual-service..."

# 0. Dump environment variables to .env so Python load_dotenv() always sees them
printenv > /app/.env || true

# 1. Pulihkan sesi login GoPay jika disediakan di secrets
if [ -n "$GOPAY_SESSION_JSON" ]; then
    echo "$GOPAY_SESSION_JSON" > /app/gopay-gateway/.GOPAY_SESI_JANGAN_DIHAPUS.json
    echo "🔑 [GOPAY] Sesi GoBiz berhasil dimuat dari environment secrets."
fi

# 2. Buat file gopay-gateway/.env jika belum ada
if [ ! -f /app/gopay-gateway/.env ]; then
    cat <<EOF > /app/gopay-gateway/.env
PORT=3005
API_KEY=RAHASIA
QRIS_STATIC=${QRIS_STATIC:-00020101021126680016ID.CO.GOPAY.WWW01189360001438922870000215ID10265038922870303UKE51440014ID.CO.QRIS.WWW0215ID10265038922870303UKE5204729953033605802ID5936TOKO DIGITAL HSN, DIGITAL & KREATIF6011DKI JAKARTA61051212162070703A01630453D8}
GOPAY_MERCHANT_ID=${GOPAY_MERCHANT_ID:-G292229702}
EOF
fi

# 3. Jalankan semua servis via PM2
echo "🟢 [PM2] Menjalankan gopay-gateway dan p2p-telegram-bot..."
exec pm2-runtime start ecosystem.config.js
