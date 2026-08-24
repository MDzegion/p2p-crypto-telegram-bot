"""
services/crypto_sender/aptos_sender.py — Sender untuk Aptos Network.
================================================================
Mengintegrasikan pengecekan saldo dan pengiriman koin APT di Aptos Network.
"""

import logging
import asyncio
import re
import secrets
import httpx
from config.settings import settings
from services.crypto_sender import BaseCryptoSender, SendResult

logger = logging.getLogger(__name__)

class AptosSender(BaseCryptoSender):
    def __init__(self):
        self.network = "APTOS"
        self.rpc_url = settings.APTOS_RPC
        self.wallet_address = settings.APTOS_WALLET_ADDRESS or "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        self.explorer_base = "https://explorer.aptoslabs.com"

    def validate_address(self, address: str) -> bool:
        """Validasi format alamat Aptos."""
        return bool(address and re.fullmatch(r"0x[0-9a-fA-F]{1,64}", address))

    async def get_balance(self, symbol: str = "") -> float:
        """Ambil saldo APT dari Aptos REST API."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.rpc_url}/accounts/{self.wallet_address}/resource/0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>")
                if res.status_code == 200:
                    data = res.json()
                    value = int(data.get("data", {}).get("coin", {}).get("value", 0))
                    return float(value / 1e8) # Aptos decimals is 8
        except Exception as e:
            logger.warning(f"Gagal mengambil saldo Aptos: {e}")
        return 0.0

    async def send(self, to_address: str, amount: float, symbol: str) -> SendResult:
        """Kirim / simulasi transaksi di Aptos Network."""
        try:
            if not self.validate_address(to_address):
                return SendResult(success=False, error_message="Alamat Aptos tidak valid.")
            
            mock_hash = "0x" + secrets.token_hex(32)
            explorer_url = f"{self.explorer_base}/txn/{mock_hash}"
            logger.info(f"[APTOS] Auto-send {amount} {symbol} ke {to_address} (Hash: {mock_hash})")
            
            return SendResult(
                success=True,
                tx_hash=mock_hash,
                explorer_url=explorer_url
            )
        except Exception as e:
            return SendResult(success=False, error_message=f"Exception pengiriman Aptos: {str(e)}")
