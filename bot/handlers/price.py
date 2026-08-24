"""
bot/handlers/price.py — Handler Cek Harga Crypto Terkini.
=========================================================
Menampilkan daftar harga beli dan jual dalam IDR untuk semua koin pendukung.
"""

import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database.connection import SessionLocal
from services.price_service import price_service
from bot.keyboards.main_menu import get_owner_button
from bot.utils.formatter import format_idr, format_datetime

logger = logging.getLogger(__name__)

# Emoji network helper
NETWORK_EMOJIS = {
    "BSC": "🟢", "ETH": "🔷", "SOLANA": "🟣", "AVAX": "🔴",
    "TRON": "❤️", "POLYGON": "🟪", "GRAVITY": "🌌",
    "BASE": "🔵", "ARB": "💎"
}

async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menampilkan harga terkini untuk seluruh aset crypto.
    Dipanggil saat user menekan tombol '💵 Cek Harga' di menu utama.
    """
    query = update.callback_query
    
    # Beritahu user sedang memproses
    await query.message.reply_chat_action(action="typing")
    
    db = SessionLocal()
    try:
        # Fetch harga dari Binance (menggunakan cache/API)
        prices_data = await price_service.get_all_prices(db)
        
        if not prices_data:
            await query.message.reply_text(
                text="⚠️ Gagal mengambil data harga saat ini. Silakan coba sesaat lagi.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu_back")
                ]])
            )
            return

        # Pemetaan network agar user tahu
        from config.assets import STOCK_ASSETS
        net_mapping = {symbol: network for symbol, network in STOCK_ASSETS}
        
        # Build text tabel harga
        text_lines = [
            "📊 <b>DAFTAR HARGA CRYPTO HARI INI</b>\n",
            "<i>Berikut adalah harga beli (Rupiah ke Crypto) & jual (Crypto ke Rupiah) terupdate:</i>\n",
        ]
        
        # Urutkan list koin agar rapi
        for symbol, data in prices_data.items():
            network = net_mapping.get(symbol, "EVM")
            net_emoji = NETWORK_EMOJIS.get(network.upper(), "🪙")
            
            buy_price = format_idr(data["buy_price_idr"])
            sell_price = format_idr(data["sell_price_idr"])
            
            text_lines.append(
                f"{net_emoji} <b>{symbol} ({network})</b>\n"
                f"   🛒 Beli: <code>{buy_price}</code>\n"
                f"   💵 Jual: <code>{sell_price}</code>\n"
            )
            
        text_lines.append(f"⏱️ <i>Update: {format_datetime(datetime.now(timezone.utc))}</i>")
        text_lines.append("⚠️ <i>Harga di atas sudah termasuk markup/markdown spread bot.</i>")
        
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
        logger.error(f"Error di show_prices: {e}", exc_info=True)
        await query.message.reply_text(
            text="⚠️ Terjadi kesalahan internal saat mengambil harga.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu_back")
            ]])
        )
    finally:
        db.close()
