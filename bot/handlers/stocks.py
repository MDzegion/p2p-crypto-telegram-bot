"""
bot/handlers/stocks.py — Handler Cek Stok Aset Crypto (Hot Wallet Balances).
==========================================================================
Menampilkan saldo cryptocurrency yang tersedia di hot wallet bot untuk dibeli user.
"""

import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database.connection import SessionLocal
from database.crud import get_all_wallet_balances
from bot.keyboards.main_menu import get_owner_button
from bot.utils.formatter import format_crypto, format_datetime

logger = logging.getLogger(__name__)

# Mapping emoji network helper
NETWORK_EMOJIS = {
    "BSC": "🟢", "ETH": "🔷", "SOLANA": "🟣", "AVAX": "🔴",
    "TRON": "❤️", "POLYGON": "🟪", "GRAVITY": "🌌",
    "BASE": "🔵", "ARB": "💎", "OPTIMISM": "🔴",
    "ROBINHOOD": "🏹", "KAIA": "🌱", "BERA": "🐻",
    "HYPEREVM": "🚀", "TON": "💎", "SUI": "💧", "APTOS": "⚡"
}

async def show_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menampilkan stok (saldo wallet) untuk semua aset crypto.
    Dipanggil saat user memilih '📦 Cek Stok' dari menu utama.
    """
    query = update.callback_query
    
    # Beritahu user sedang memproses
    await query.message.reply_chat_action(action="typing")
    
    db = SessionLocal()
    try:
        # Ambil semua saldo wallet yang tercatat di database
        balances = get_all_wallet_balances(db)
        if not balances:
            try:
                from main import _job_sync_wallet_balances
                await _job_sync_wallet_balances()
                db.close()
                db = SessionLocal()
                balances = get_all_wallet_balances(db)
            except Exception as sync_err:
                logger.warning(f"On-demand stock sync error: {sync_err}")
        
        text_lines = [
            "📦 <b>STOK CRYPTO YANG TERSEDIA</b>\n",
            "<i>Berikut adalah saldo koin di hot wallet kami yang siap dikirim secara instan:</i>\n",
        ]
        
        if not balances:
            text_lines.append("⚠️ <i>Belum ada data stok tercatat. Saldo sedang disinkronisasikan...</i>")
        else:
            for wallet in balances:
                net_upper = wallet.network.upper()
                emoji = NETWORK_EMOJIS.get(net_upper, "🪙")
                bal_val = float(wallet.balance)
                
                # Format saldo crypto: tampilkan nominal asli (termasuk 0)
                formatted_bal = format_crypto(bal_val, wallet.symbol)
                if bal_val > 0:
                    status_str = f"<code>{formatted_bal}</code> ✅"
                else:
                    status_str = f"<code>{formatted_bal}</code> (belum ada stok)"
                
                # Sembunyikan bagian tengah wallet address untuk alasan privasi
                addr = wallet.address or ""
                masked_addr = f"{addr[:6]}...{addr[-6:]}" if len(addr) > 12 else (addr or "Verified Hot Wallet")
                
                text_lines.append(
                    f"{emoji} <b>{wallet.symbol} ({wallet.network})</b>\n"
                    f"   💰 Stok: {status_str}\n"
                    f"   📍 Address: <code>{masked_addr}</code>\n"
                )
                
        text_lines.append(f"⏱️ <i>Update: {format_datetime(datetime.now(timezone.utc))}</i>")
        text_lines.append("\n💡 <i>Seluruh stok koin aktif 24/7 dan disinkronisasi dengan blockchain secara real-time.</i>")
        
        message_text = "\n".join(text_lines)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu_back")],
            [get_owner_button()]
        ]
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error di show_stocks: {e}", exc_info=True)
        await query.message.reply_text(
            text="⚠️ Gagal mengambil data stok saldo wallet. Silakan hubungi admin.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu_back")
            ]])
        )
    finally:
        db.close()
