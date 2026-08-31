"""
services/gopay_service.py — GoPay / Gopiz API Gateway Integration Client
========================================================================
Berkomunikasi dengan API Gateway Mandiri GoPay (ahmadzakiyox/gopay-api-gateaway)
untuk request QRIS Dinamis dan verifikasi pembayaran mutasi secara otomatis.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class GopayGatewayService:
    def __init__(self):
        self.base_url = (settings.GOPAY_GATEWAY_URL or "http://127.0.0.1:3005").rstrip("/")
        self.api_key = settings.GOPAY_API_KEY or "RAHASIA"

    async def check_payment(self, amount: int, trx_id: str) -> Optional[Dict[str, Any]]:
        """
        Mengecek mutasi pembayaran masuk untuk nominal dan trx_id spesifik.
        
        Returns:
            dict: {
                "paid": bool,
                "transaction": dict
            }
        """
        try:
            url = f"{self.base_url}/check-payment"
            params = {
                "amount": amount,
                "trx_id": trx_id,
                "api_key": self.api_key
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    json_res = res.json()
                    return {
                        "paid": bool(json_res.get("paid")),
                        "transaction": json_res.get("transaction")
                    }
                return {"paid": False, "transaction": None}
        except Exception as e:
            logger.warning(f"GopayGatewayService check_payment error ({trx_id}): {e}")
            return {"paid": False, "transaction": None}

    async def get_recent_transactions(
        self,
        start_time: int = None,
        end_time: int = None,
        page_size: int = 100,
    ) -> list:
        """
        Mengambil riwayat mutasi transaksi dari gateway GoPay
        (endpoint GET /transactions).

        Args:
            start_time (int, optional): Timestamp unix detik awal (default 3 hari lalu).
            end_time (int, optional): Timestamp unix detik akhir (default sekarang).
            page_size (int, optional): Jumlah transaksi maksimal (default 100).

        Returns:
            list: Daftar transaksi (dict) atau [] jika gagal/tidak ada.
        """
        try:
            params = {"api_key": self.api_key, "pageSize": page_size}
            if start_time is not None:
                params["startTime"] = start_time
            if end_time is not None:
                params["endTime"] = end_time

            url = f"{self.base_url}/transactions"
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, params=params)
                if res.status_code != 200:
                    logger.warning(f"GET /transactions HTTP {res.status_code}")
                    return []

                data = res.json()

            # Parsing defensif: response bisa berupa list langsung
            # atau dict {success, data: [...]}
            if isinstance(data, list):
                return data

            inner = data.get("data")
            if isinstance(inner, list):
                return inner
            if isinstance(inner, dict):
                for key in ("transactions", "items", "list", "mutasi"):
                    val = inner.get(key)
                    if isinstance(val, list):
                        return val
            return []
        except Exception as e:
            logger.warning(f"GopayGatewayService get_recent_transactions error: {e}")
            return []


gopay_service = GopayGatewayService()
