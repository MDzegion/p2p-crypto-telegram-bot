"""
bot/utils/validator.py — Fungsi Validasi Input untuk P2P Crypto Bot.
====================================================================
Menangani validasi alamat wallet berdasarkan blockchain network (EVM, Solana, Tron, LTC)
serta validasi nominal rupiah dan crypto.
"""

import re
import base58
from web3 import Web3

def validate_wallet_address(address: str, network: str) -> bool:
    """
    Validasi alamat wallet berdasarkan network.
    
    Networks:
      - BSC, ETH, AVAX, POLYGON, BASE, ARB, GRAVITY (EVM)
      - SOLANA
      - TRON
    """
    if not address:
        return False
        
    address = address.strip()
    net = network.upper()

    # --- 1. EVM Chains ---
    evm_chains = [
        "BSC", "ETH", "AVAX", "POLYGON", "BASE", "ARB", "GRAVITY",
        "OPTIMISM", "ROBINHOOD", "KAIA", "BERA", "HYPEREVM", "ERC20", "BEP20",
    ]
    if net in evm_chains:
        try:
            return Web3.is_address(address)
        except Exception:
            return False

    # --- 2. Solana ---
    elif net == "SOLANA":
        try:
            if not (32 <= len(address) <= 44):
                return False
            # Cek decoding base58
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False

    # --- 3. TRON ---
    elif net == "TRON":
        try:
            if len(address) != 34 or not address.startswith("T"):
                return False
            # Check base58 encoding
            base58.b58decode(address)
            return True
        except Exception:
            return False

    # --- 4. TON ---
    elif net == "TON":
        if re.fullmatch(r"(?:0|-1):[0-9a-fA-F]{64}", address):
            return True
        if not re.fullmatch(r"(?:EQ|UQ)[A-Za-z0-9_-]{46}", address):
            return False
        try:
            from tonsdk.utils import Address
            Address(address).to_string(is_user_friendly=False)
            return True
        except Exception:
            return False

    # --- 5. SUI ---
    elif net == "SUI":
        return bool(re.fullmatch(r"0x[0-9a-fA-F]{64}", address))

    # --- 6. APTOS ---
    elif net == "APTOS":
        return bool(re.fullmatch(r"0x[0-9a-fA-F]{1,64}", address))

    return False


def validate_amount_idr(amount_str: str) -> tuple[bool, int]:
    """
    Memvalidasi dan memparse string nominal rupiah.
    Minimal order adalah Rp 5.000 (sesuai spesifikasi client).
    
    Returns:
        tuple: (is_valid: bool, parsed_amount: int)
    """
    try:
        # Hapus format non-numerik seperti "Rp", titik, koma, spasi
        cleaned = re.sub(r"[^\d]", "", amount_str)
        if not cleaned:
            return False, 0
            
        amount = int(cleaned)
        
        # Cek batas minimal 5.000 IDR
        if amount < 5000:
            return False, amount
            
        return True, amount
    except Exception:
        return False, 0


def validate_crypto_amount(amount_str: str) -> tuple[bool, float]:
    """
    Memvalidasi dan memparse string nominal crypto (untuk sell flow).
    Mendukung format desimal menggunakan titik atau koma.
    
    Returns:
        tuple: (is_valid: bool, parsed_amount: float)
    """
    try:
        # Ganti koma dengan titik untuk desimal standar Python
        cleaned = amount_str.replace(",", ".").strip()
        
        # Validasi format float
        if not re.match(r"^\d+(\.\d+)?$", cleaned):
            return False, 0.0
            
        amount = float(cleaned)
        if amount <= 0:
            return False, 0.0
            
        return True, amount
    except Exception:
        return False, 0.0
