"""
config/assets.py — Master Daftar Aset (Symbol, Network) yang Dipantau Stoknya.
==============================================================================
Satu sumber kebenaran untuk sinkronisasi saldo hot wallet per (network, symbol).
Semua pasangan yang bisa dibeli/dijual user harus terdaftar di sini agar
stoknya muncul dengan nominal asli di fitur "Cek Stok".
"""

# Pasangan (SYMBOL, NETWORK) yang stoknya disinkronkan dari blockchain.
# Termasuk native coin tiap chain + token yang diperjualbelikan bot.
STOCK_ASSETS = [
    # --- EVM: USDT / USDC / Native ---
    ("USDT", "BSC"),
    ("USDT", "POLYGON"),
    ("USDT", "ARB"),
    ("USDT", "ETH"),
    ("USDC", "BASE"),
    ("USDC", "ETH"),
    ("USDC", "BSC"),
    ("USDC", "ARB"),
    ("USDC", "POLYGON"),
    ("BNB", "BSC"),
    ("ETH", "BASE"),
    ("ETH", "ARB"),
    ("ETH", "OPTIMISM"),
    ("ETH", "ROBINHOOD"),
    ("ETH", "ETH"),
    ("MATIC", "POLYGON"),
    ("ARB", "ARB"),
    ("AVAX", "AVAX"),
    ("KAIA", "KAIA"),
    ("BERA", "BERA"),
    ("HYPE", "HYPEREVM"),
    ("G", "GRAVITY"),
    # --- Non-EVM: native + token ---
    ("SOL", "SOLANA"),
    ("USDT", "SOLANA"),
    ("USDC", "SOLANA"),
    ("TRX", "TRON"),
    ("TON", "TON"),
    ("USDT", "TON"),
    ("SUI", "SUI"),
    ("APT", "APTOS"),
]

# Alamat kontrak token untuk network non-EVM (untuk cek saldo token).
NON_EVM_TOKENS = {
    "SOLANA": {
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    },
    "TRON": {
        "USDT": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    },
    "TON": {
        "USDT": "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs",
    },
}

# Gambar QRIS Statis merchant (dikirim ke user untuk pembayaran manual).
QRIS_STATIC_IMAGE = "Qris statis.jpeg"
