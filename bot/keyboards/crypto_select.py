"""
bot/keyboards/crypto_select.py — Keyboard Pilihan Crypto & Pembayaran.
=====================================================================
Menyediakan inline keyboard untuk memilih aset cryptocurrency.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards.main_menu import get_owner_button

# Mapping simbol ke daftar network yang tersedia untuk Beli/Jual Crypto
BUY_NETWORKS_BY_SYMBOL = {
    "USDT": ["BSC", "POLYGON", "ARB", "TON", "SOLANA", "ETH"],
    "USDC": ["BASE", "ETH", "BSC", "ARB", "SOLANA", "POLYGON"],
    "ETH": ["BASE", "ARB", "OPTIMISM", "ROBINHOOD", "ETH"],
    "SOL": ["SOLANA"],
    "TRX": ["TRON"],
    "BNB": ["BSC"],
    "SUI": ["SUI"],
    "TON": ["TON"],
    "POL": ["POLYGON"],
    "ARB": ["ARB"],
    "AVAX": ["AVAX"],
    "KAIA": ["KAIA"],
    "BERA": ["BERA"],
    "APT": ["APTOS"],
    "HYPE": ["HYPEREVM"],
}

SYMBOL_EMOJIS = {
    "USDT": "🟢", "USDC": "🔵", "ETH": "🔷", "SOL": "🟣",
    "TRX": "❤️", "BNB": "🟡", "SUI": "💧", "TON": "💎",
    "POL": "🟪", "ARB": "💎", "AVAX": "🔴", "KAIA": "🌱",
    "BERA": "🐻", "APT": "⚡", "HYPE": "🚀"
}


def _get_symbol_keyboard(prefix: str, back_callback: str) -> InlineKeyboardMarkup:
    """Keyboard pilih simbol untuk alur beli (buy_sym_*) atau jual (sell_sym_*)."""
    keyboard = []
    row = []
    for sym in BUY_NETWORKS_BY_SYMBOL:
        emoji = SYMBOL_EMOJIS.get(sym, "🪙")
        row.append(InlineKeyboardButton(f"{emoji} {sym}", callback_data=f"{prefix}_sym_{sym}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Menu", callback_data=back_callback)])
    keyboard.append([get_owner_button()])
    return InlineKeyboardMarkup(keyboard)


def _get_network_keyboard(symbol: str, prefix: str, back_callback: str) -> InlineKeyboardMarkup:
    """Keyboard pilih jaringan untuk alur beli (buy_net_*) atau jual (sell_net_*)."""
    symbol = symbol.upper()
    networks = BUY_NETWORKS_BY_SYMBOL.get(symbol, ["BSC"])

    keyboard = [[InlineKeyboardButton(f"🌐 {net}", callback_data=f"{prefix}_net_{symbol}_{net}")] for net in networks]
    keyboard.append([InlineKeyboardButton("🔙 Kembali (Pilih Koin)", callback_data=back_callback)])
    keyboard.append([get_owner_button()])
    return InlineKeyboardMarkup(keyboard)


def get_buy_symbol_keyboard() -> InlineKeyboardMarkup:
    return _get_symbol_keyboard("buy", "menu_back")


def get_buy_network_keyboard(symbol: str) -> InlineKeyboardMarkup:
    return _get_network_keyboard(symbol, "buy", "buy_back_symbols")


def get_sell_symbol_keyboard() -> InlineKeyboardMarkup:
    return _get_symbol_keyboard("sell", "menu_back")


def get_sell_network_keyboard(symbol: str) -> InlineKeyboardMarkup:
    return _get_network_keyboard(symbol, "sell", "sell_back_symbols")
