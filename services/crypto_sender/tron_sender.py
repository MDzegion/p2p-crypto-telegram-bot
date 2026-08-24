"""
services/crypto_sender/tron_sender.py — Sender untuk TRON (TRX).
==================================================================
Menangani pengiriman koin TRX native ke wallet customer menggunakan tronpy.
"""

import logging
import asyncio
from config.settings import settings
from services.crypto_sender import BaseCryptoSender, SendResult

# Tronpy imports
try:
    from tronpy import Tron
    from tronpy.keys import PrivateKey, to_hex_address
    from tronpy.providers.http import HTTPProvider
    TRONPY_AVAILABLE = True
except ImportError:
    TRONPY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Alamat kontrak USDT TRC-20
USDT_TRC20 = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

class TronSender(BaseCryptoSender):
    def __init__(self):
        self.explorer_base = "https://tronscan.org"
        self.wallet_address = settings.TRX_WALLET_ADDRESS
        self.private_key_hex = settings.TRX_PRIVATE_KEY

    def validate_address(self, address: str) -> bool:
        """Validasi address TRON: dimulai dengan huruf T dan panjang 34 karakter."""
        try:
            if not address or len(address) != 34 or not address.startswith("T"):
                return False
            # Jika library tronpy terinstall, gunakan check internal
            if TRONPY_AVAILABLE:
                from tronpy.keys import is_address
                return is_address(address)
            return True
        except Exception:
            return False

    async def get_balance(self, symbol: str = "") -> float:
        """Mengambil saldo TRX native atau token TRC-20 (USDT)."""
        sym = symbol.upper() if symbol else ""
        if sym in ("USDT",):
            return await self._get_trc20_balance(USDT_TRC20)

        if not TRONPY_AVAILABLE:
            logger.error("Library tronpy tidak terinstall.")
            return 0.0
        try:
            # Menggunakan HTTP client tronpy
            client = Tron() # Default terhubung ke Mainnet
            balance_sun = await asyncio.to_thread(client.get_account_balance, self.wallet_address)
            # 1 TRX = 1,000,000 SUN
            balance = float(balance_sun)
            return balance
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", 0)
            if e.__class__.__name__ == "AddressNotFound":
                logger.warning("Wallet TRON belum tercatat on-chain: %s", self.wallet_address)
            elif status in (429, 500, 502, 503):
                logger.warning("Gagal mengambil saldo TRX (HTTP %s): %s", status, e)
            else:
                logger.error(f"Gagal mengambil saldo TRX: {e}", exc_info=True)
            return 0.0

    async def _get_trc20_balance(self, contract_address: str) -> float:
        """
        Mengambil saldo token TRC-20 (USDT) milik wallet bot.
        """
        if not TRONPY_AVAILABLE:
            logger.error("Library tronpy tidak terinstall.")
            return 0.0
        try:
            client = Tron(provider=HTTPProvider(timeout=20.0))
            contract = await asyncio.to_thread(client.get_contract, contract_address)
            raw_balance = await asyncio.to_thread(
                contract.functions.balanceOf, self.wallet_address
            )
            try:
                decimals = int(await asyncio.to_thread(contract.functions.decimals))
            except Exception:
                decimals = 6
            return float(int(raw_balance) / (10 ** decimals))
        except Exception as e:
            logger.error(f"Gagal mengambil saldo TRC-20: {e}", exc_info=True)
            return 0.0

    async def send(self, to_address: str, amount: float, symbol: str) -> SendResult:
        """Mengirim TRX native atau USDT TRC-20."""
        if not TRONPY_AVAILABLE:
            return SendResult(
                success=False,
                error_message="Library tronpy tidak tersedia di server ini."
            )
        try:
            # Validasi input
            if not self.validate_address(to_address):
                return SendResult(success=False, error_message="Alamat wallet TRON tidak valid.")

            # Load private key
            try:
                priv_key = PrivateKey(bytes.fromhex(self.private_key_hex))
            except Exception as key_err:
                return SendResult(
                    success=False,
                    error_message=f"Gagal memuat TRON Private Key (pastikan format hex): {key_err}"
                )

            client = Tron(provider=HTTPProvider(timeout=20.0))
            symbol_upper = symbol.upper()

            if symbol_upper == "USDT":
                token_balance = await self.get_balance("USDT")
                if token_balance < amount:
                    return SendResult(
                        success=False,
                        error_message=(
                            f"Saldo USDT TRC-20 tidak cukup. Saldo: {token_balance}, "
                            f"Kebutuhan: {amount}"
                        ),
                    )
                contract = await asyncio.to_thread(client.get_contract, USDT_TRC20)

                try:
                    address_param = to_hex_address(to_address)[2:].lower().zfill(64)
                    amount_param = hex(int(amount * 1_000_000))[2:].zfill(64)
                    energy = await asyncio.to_thread(
                        client.get_estimated_energy,
                        self.wallet_address,
                        USDT_TRC20,
                        "transfer(address,uint256)",
                        address_param + amount_param,
                    )
                    chain_params = await asyncio.to_thread(client.get_chain_parameters)
                    energy_fee = next(
                        int(item["value"])
                        for item in chain_params
                        if item.get("key") == "getEnergyFee"
                    )
                    trx_cost = energy * energy_fee / 1_000_000
                    from services.price_service import price_service
                    price = await price_service.get_price("TRX")
                    if not price:
                        return SendResult(
                            success=False,
                            error_message="MANUAL_REVIEW: Harga TRX tidak tersedia untuk estimasi gas.",
                        )
                    gas_idr = trx_cost * float(price["buy_price_idr"])
                    if gas_idr > 2000:
                        return SendResult(
                            success=False,
                            error_message=(
                                "MANUAL_REVIEW: Estimasi biaya energi TRON "
                                f"{gas_idr:,.0f} IDR melebihi batas 2.000 IDR."
                            ),
                        )
                except Exception as gas_err:
                    logger.warning("Gagal estimasi energi TRC-20: %s", gas_err)
                    return SendResult(
                        success=False,
                        error_message="MANUAL_REVIEW: Estimasi energi TRC-20 tidak tersedia.",
                    )

                def _build_and_sign():
                    return (
                        contract.functions.transfer(
                            to_address, int(amount * 1_000_000)
                        )
                        .with_owner(self.wallet_address)
                        .fee_limit(10_000_000)
                        .build()
                        .sign(priv_key)
                    )
            else:
                balance = await self.get_balance()
                if balance < amount:
                    return SendResult(
                        success=False,
                        error_message=f"Saldo TRX tidak cukup. Saldo: {balance} TRX, Kebutuhan: {amount} TRX"
                    )
                amount_sun = int(amount * 1_000_000)

                def _build_and_sign():
                    return (
                        client.trx.transfer(self.wallet_address, to_address, amount_sun)
                        .build()
                        .sign(priv_key)
                    )

            txn = await asyncio.to_thread(_build_and_sign)

            # Broadcast transaksi
            result = await asyncio.to_thread(txn.broadcast)
            
            # Cek hasil broadcast
            tx_hash = result.get("txid", "")
            if not tx_hash:
                return SendResult(
                    success=False,
                    error_message=f"Gagal mendapatkan txid dari response broadcast: {result}"
                )

            # Tunggu konfirmasi transaksi
            # Di TRON, broadcast yang sukses biasanya langsung masuk mempool.
            # Kita bisa asumsikan terkirim jika broadcast mengembalikan status SUCCESS
            # atau memiliki txid.
            logger.info(f"Transaksi TRON berhasil dikirim. Hash: {tx_hash}")
            explorer_url = f"{self.explorer_base}/#/transaction/{tx_hash}"
            
            return SendResult(
                success=True,
                tx_hash=tx_hash,
                explorer_url=explorer_url
            )

        except Exception as e:
            logger.error(f"Error saat mengirim TRX: {e}", exc_info=True)
            return SendResult(
                success=False,
                error_message=f"Exception saat pengiriman TRON: {str(e)}"
            )
