"""
bot/utils/messages.py — Template Pesan untuk P2P Crypto Bot.
============================================================
Definisi teks pesan dalam Bahasa Indonesia dengan formatting HTML.
"""

WELCOME_MESSAGE = (
    "👋 <b>Halo {name}!</b>\n\n"
    "Selamat datang di <b>HSN STORE bot</b> — P2P Crypto Trading Automation. 🚀\n\n"
    "🆔 <b>ID Telegram:</b> <code>{chat_id}</code>\n"
    "🏆 <b>Member Ke:</b> #{user_num}\n"
    "👥 <b>Total Pengguna:</b> {total_users} member\n"
    "✅ <b>Total Transaksi Berhasil:</b> {total_success}\n\n"
    "Silakan pilih menu di bawah ini untuk memulai transaksi:"
)

SNK_TEXT = (
    "⚠️ <b>SYARAT & KETENTUAN (S&K)</b>\n\n"
    "1. Bot ini beroperasi secara otomatis 24/7 untuk transaksi instan.\n"
    "2. Minimal pembelian/penjualan adalah <b>Rp 5.000</b>.\n"
    "3. Biaya transaksi (fee) dihitung secara fixed tier transparan sesuai nominal transaksi.\n"
    "4. Pastikan alamat wallet crypto Anda benar. Kesalahan input alamat bukan tanggung jawab kami!\n"
    "5. Transaksi tidak dapat dibatalkan setelah pembayaran diverifikasi.\n"
    "6. Jika mengalami kendala, hubungi owner dengan tombol <b>Hubungi Owner</b>.\n"
    "7. Apabila ada saran atau masukan untuk bot ini silakan chat admin untuk dilakukan perbaikan dan pembaruan.\n"
    "8. Tidak menerima top up USD ke Address Exness atau HashKey."
)

ORDER_SUMMARY_BUY = (
    "🛒 <b>RINGKASAN ORDER PEMBELIAN</b>\n\n"
    "📝 <b>ID Order:</b> <code>{order_id}</code>\n"
    "🪙 <b>Aset:</b> {crypto_amount_str}\n"
    "📈 <b>Kurs:</b> {price_per_unit_str} / unit\n"
    "────────────────────\n"
    "💳 <b>Nominal Bayar:</b> {nominal_idr_str}\n"
    "🔌 <b>Fee Layanan (dipotong):</b> -{fee_idr_str}\n"
    "💰 <b>Nilai Koin Diterima:</b> <b>{received_idr_str}</b>\n\n"
    "📍 <b>Wallet Penerima:</b>\n<code>{buyer_wallet}</code>\n\n"
    "Silakan klik tombol konfirmasi di bawah jika data sudah benar."
)

ORDER_SUMMARY_SELL = (
    "📈 <b>RINGKASAN ORDER PENJUALAN</b>\n\n"
    "📝 <b>ID Order:</b> <code>{order_id}</code>\n"
    "🪙 <b>Kirim Aset:</b> {crypto_amount_str}\n"
    "📈 <b>Kurs:</b> {price_per_unit_str} / unit\n"
    "────────────────────\n"
    "💰 <b>Nominal Bersih (IDR):</b> <b>{nominal_idr_str}</b>\n"
    "🔌 <b>Fee Layanan:</b> {fee_idr_str}\n\n"
    "🏦 <b>Rekening Penerima Anda:</b>\n"
    "• Bank: {bank_name}\n"
    "• No Rekening: <code>{bank_acc}</code>\n"
    "• Atas Nama: {bank_holder}\n\n"
    "Silakan klik konfirmasi di bawah untuk memproses penjualan."
)
