import asyncio
from datetime import datetime
from database.connection import SessionLocal
from database.models import Order, AuditLog
from bot.utils.telegram_utils import safe_send_message
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.formatter import format_crypto
from telegram.ext import ApplicationBuilder
from config.settings import settings

async def main():
    db = SessionLocal()
    try:
        o = db.query(Order).filter(Order.order_id == 'SWAP-20260830160826-640').first()
        if not o:
            print("Order not found")
            return
        o.status = 'completed'
        o.payout_tx_hash = '0x9ec9f7aeb391242df7ed9d4cd39f176324d769b83de4433112a6bfaf68138875'
        o.completed_at = datetime.utcnow()
        db.add(AuditLog(
            telegram_id=o.telegram_id,
            action='PAYOUT_SUCCESS_ONCHAIN',
            order_id=o.order_id,
            from_status='manual_review',
            to_status='completed',
            details='Payout on-chain BSC: 0x9ec9f7aeb391242df7ed9d4cd39f176324d769b83de4433112a6bfaf68138875'
        ))
        db.commit()

        app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        msg = (
            f"🎉 <b>CONVERT BERHASIL!</b>\n\n"
            f"ID Order: <code>{o.order_id}</code>\n"
            f"Setor: {format_crypto(o.crypto_amount, o.crypto_symbol)} ({o.network})\n"
            f"Terima: <b>{format_crypto(o.target_crypto_amount, o.target_crypto_symbol)} ({o.target_network})</b>\n"
            f"Wallet Tujuan: <code>{o.buyer_wallet}</code>\n\n"
            f"TX Hash Pengiriman:\n<code>{o.payout_tx_hash}</code>\n\n"
            f"🔗 <a href=\"https://bscscan.com/tx/{o.payout_tx_hash}\">Cek di Blockchain Explorer</a>\n\n"
            f"Koin tujuan telah berhasil dikirimkan ke wallet Anda. Terima kasih! 🙏"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu Utama", callback_data="menu_back")]])
        await safe_send_message(app.bot, o.telegram_id, msg, reply_markup=kb)
        print("Success notification sent to user!")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
