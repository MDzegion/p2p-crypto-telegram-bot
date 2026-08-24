"""
scratch/test_e2e_engine.py — E2E Test Transaction Engine (DB sementara, tanpa jaringan/Telegram).
==================================================================================================
Menguji alur end-to-end inti:
  1. Fee engine (USD/ALTCOIN/CONVERT + surcharge)
  2. Factory sender 16 network
  3. Swap: TX hash -> verifikasi -> CRYPTO_CONFIRMED -> auto-payout -> COMPLETED
  4. Swap: auto-scan riwayat (tanpa hash) -> terverifikasi
  5. Guard: reuse hash antar order & anti double-payout
  6. Sell: deposit terverifikasi -> CRYPTO_CONFIRMED
  7. Buy GoPay QRIS: pending -> finalize -> COMPLETED
  8. Topup: matcher riwayat mutasi

DB SQLite sementara (TIDAK menyentuh p2p_bot.db).
"""

import os
import sys
import asyncio
import tempfile
from datetime import datetime, timedelta

# --- DB sementara SEBELUM import settings/main ---
_tmp_db = os.path.join(tempfile.gettempdir(), "opencode", "e2e_test_bot.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal, engine, Base
from database.models import User, Order, AuditLog, WalletBalance
from services.fee_service import calculate_fee_idr
from services.crypto_sender import CryptoSenderFactory
import services.tx_verifier as tx_verifier
import services.payout_service as payout_service

# ---------------- Mocks ----------------
PAYOUT_CALLS = []
VERIFY_HASHES = set()   # hash yang dianggap valid


async def fake_verify(network, symbol, tx_hash, expected_wallet, expected_amount):
    if tx_hash in VERIFY_HASHES:
        return {"verified": True, "amount": expected_amount, "from_address": "0xUser", "reason": "OK"}
    return {"verified": False, "amount": 0.0, "from_address": "", "reason": "not found"}


async def fake_recent_incoming(network, symbol, wallet, min_amount=0.0, limit=20):
    if wallet == "AUTOSCAN_WALLET":
        return [{"tx_hash": "AUTOHASH1", "amount": min_amount, "from_address": "0xUser"}]
    return []


async def fake_payout(order):
    PAYOUT_CALLS.append(order.order_id)
    return {"success": True, "tx_hash": "0xPayoutHash", "explorer_url": "https://explorer/tx/0xPayoutHash", "error_message": ""}


# ---------------- Test 1: Fee engine ----------------
def test_fee_engine():
    print("\n--- 1. FEE ENGINE ---")
    assert calculate_fee_idr(5000, "USD") == 3000
    assert calculate_fee_idr(1000000, "USD") == 14000
    assert calculate_fee_idr(5000, "ALTCOIN") == 3000
    assert calculate_fee_idr(550000, "ALTCOIN") == 11500
    assert calculate_fee_idr(7000, "CONVERT") == 3500
    assert calculate_fee_idr(50000, "CONVERT") == 5500
    assert calculate_fee_idr(5000, "ALTCOIN", symbol="ETH", network="ETH", is_outgoing=True) == 5000
    assert calculate_fee_idr(5000, "ALTCOIN", symbol="ETH", network="ETH", is_outgoing=False) == 3000
    assert calculate_fee_idr(5000, "ALTCOIN", symbol="TRX", network="TRON", is_outgoing=True) == 5000
    assert calculate_fee_idr(5000, "ALTCOIN", symbol="TRX", network="TRON", is_outgoing=False) == 3000
    print("[PASS] fee tier + surcharge")


# ---------------- Test 2: Sender factory ----------------
def test_sender_factory():
    print("\n--- 2. SENDER FACTORY (16 network) ---")
    networks = ["BSC", "ETH", "AVAX", "POLYGON", "BASE", "ARB", "OPTIMISM", "ROBINHOOD",
                "KAIA", "BERA", "HYPEREVM", "SOLANA", "TRON", "TON", "SUI", "APTOS"]
    for net in networks:
        assert CryptoSenderFactory.get_sender(net) is not None
    print("[PASS] 16 senders resolved")


# ---------------- Test 3-5: Swap lifecycle ----------------
async def test_swap_lifecycle(db):
    print("\n--- 3. SWAP: hash -> verify -> payout -> COMPLETED ---")
    VERIFY_HASHES.add("0xValidSwapHash")
    order = Order(
        order_id="SWAP-E2E-1", telegram_id=777001, order_type="swap",
        crypto_symbol="USDT", network="BSC", crypto_amount=100.0,
        target_crypto_symbol="ETH", target_network="BASE", target_crypto_amount=0.015,
        price_per_unit=0, nominal_idr=1600000, fee_idr=8500, total_idr=1600000,
        fee_category="CONVERT",
        buyer_wallet="0xBuyer111111111111111111111111111111111111",
        deposit_wallet="0xDeposit111111111111111111111111111111111111",
        deposit_tx_hash="0xValidSwapHash",
        status="WAITING_CRYPTO_DEPOSIT", quoted_at=datetime.utcnow(),
        quote_expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(order); db.commit()

    from services.detector import deposit_detector
    await deposit_detector.scan_incoming_deposits(bot_app=None)
    db.refresh(order)
    assert order.status == "COMPLETED", f"status={order.status}"
    assert order.payout_tx_hash == "0xPayoutHash"
    assert PAYOUT_CALLS.count("SWAP-E2E-1") == 1, "payout harus tepat 1x"
    audits = db.query(AuditLog).filter(AuditLog.order_id == "SWAP-E2E-1").all()
    actions = [a.action for a in audits]
    assert "DEPOSIT_CONFIRMED_ONCHAIN" in actions and "SWAP_COMPLETED" in actions
    print("[PASS] COMPLETED, payout 1x, audit OK")

    print("--- 4. GUARD anti double-payout (scan ulang) ---")
    await deposit_detector.scan_incoming_deposits(bot_app=None)
    assert PAYOUT_CALLS.count("SWAP-E2E-1") == 1
    print("[PASS] tidak double-payout")

    print("--- 5. GUARD reuse hash antar order ---")
    order2 = Order(
        order_id="SWAP-E2E-2", telegram_id=777002, order_type="swap",
        crypto_symbol="USDT", network="BSC", crypto_amount=100.0,
        target_crypto_symbol="SOL", target_network="SOLANA", target_crypto_amount=1.0,
        price_per_unit=0, nominal_idr=1600000, fee_idr=8500, total_idr=1600000,
        fee_category="CONVERT",
        buyer_wallet="0xBuyer222222222222222222222222222222222222",
        deposit_wallet="0xDeposit222222222222222222222222222222222222",
        deposit_tx_hash="0xValidSwapHash",  # sama dgn order1
        status="WAITING_CRYPTO_DEPOSIT", quoted_at=datetime.utcnow(),
        quote_expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(order2); db.commit()
    await deposit_detector.scan_incoming_deposits(bot_app=None)
    db.refresh(order2)
    # hash sudah dipakai order1 -> harus tetap menunggu
    assert order2.status == "WAITING_CRYPTO_DEPOSIT", f"status={order2.status}"
    print("[PASS] hash reuse ditolak")


# ---------------- Test 6: Auto-scan tanpa hash ----------------
async def test_autoscan(db):
    print("\n--- 6. SWAP: auto-scan riwayat (tanpa hash) ---")
    VERIFY_HASHES.add("AUTOHASH1")
    order = Order(
        order_id="SWAP-E2E-3", telegram_id=777003, order_type="swap",
        crypto_symbol="USDT", network="BSC", crypto_amount=50.0,
        target_crypto_symbol="TON", target_network="TON", target_crypto_amount=0.5,
        price_per_unit=0, nominal_idr=800000, fee_idr=7000, total_idr=800000,
        fee_category="CONVERT",
        buyer_wallet="0xBuyer333333333333333333333333333333333333",
        deposit_wallet="AUTOSCAN_WALLET",
        status="WAITING_CRYPTO_DEPOSIT", quoted_at=datetime.utcnow(),
        quote_expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(order); db.commit()
    from services.detector import deposit_detector
    await deposit_detector.scan_incoming_deposits(bot_app=None)
    db.refresh(order)
    assert order.status == "COMPLETED", f"status={order.status}"
    assert order.deposit_tx_hash == "AUTOHASH1"
    print("[PASS] auto-scan menemukan deposit -> payout")


# ---------------- Test 7: Sell ----------------
async def test_sell(db):
    print("\n--- 7. SELL: deposit terverifikasi -> CRYPTO_CONFIRMED ---")
    VERIFY_HASHES.add("0xSellHash")
    order = Order(
        order_id="SELL-E2E-1", telegram_id=777004, order_type="sell",
        crypto_symbol="USDT", network="BSC", crypto_amount=10.0,
        price_per_unit=16000, nominal_idr=160000, fee_idr=4000, total_idr=156000,
        fee_category="USD",
        buyer_wallet="BCA | 1234567890 | Budi",
        deposit_wallet="0xDeposit111111111111111111111111111111111111",
        deposit_tx_hash="0xSellHash",
        status="WAITING_CRYPTO_DEPOSIT",
        expired_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(order); db.commit()
    from services.detector import deposit_detector
    await deposit_detector.scan_incoming_deposits(bot_app=None)
    db.refresh(order)
    assert order.status == "CRYPTO_CONFIRMED", f"status={order.status}"
    print("[PASS] sell deposit terverifikasi, menunggu transfer IDR admin")


# ---------------- Test 8: Buy GoPay finalize ----------------
async def test_buy_gopay(db):
    print("\n--- 8. BUY GoPay QRIS: pending -> finalize -> COMPLETED ---")
    order = Order(
        order_id="BUY-E2E-1", telegram_id=777005, order_type="buy",
        crypto_symbol="SOL", network="SOLANA", crypto_amount=2.0,
        price_per_unit=800000, nominal_idr=1600000, fee_idr=8500, total_idr=1608500,
        fee_category="ALTCOIN",
        buyer_wallet="SolanaBuyerWallet1111111111111111111111111",
        payment_method="GOPAY_QRIS",
        status="pending",
        expired_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(order); db.commit()

    from bot.handlers.buy import finalize_gopay_buy_payment
    await finalize_gopay_buy_payment(db, order, bot=None)
    db.refresh(order)
    assert order.status == "completed", f"status={order.status}"
    assert order.payout_tx_hash == "0xPayoutHash"
    print("[PASS] buy GoPay -> paid -> completed + payout")

    print("--- 8b. Idempotent: finalize ulang tidak mengubah ---")
    await finalize_gopay_buy_payment(db, order, bot=None)
    db.refresh(order)
    assert order.status == "completed"
    assert PAYOUT_CALLS.count("BUY-E2E-1") == 1
    print("[PASS] idempotent")


# ---------------- Test 9: Topup matcher ----------------
def test_topup_matcher(db):
    print("\n--- 9. TOPUP: matcher riwayat mutasi /transactions ---")
    from main import _match_transaction_for_topup
    from database.models import TopupOrder

    topup = TopupOrder(topup_id="TP-1", telegram_id=777006, amount_idr=25000,
                       status="PENDING", created_at=datetime.utcnow())
    used = set()

    tx_ok = {"transaction_id": "TX-1", "amount": 25000,
             "transaction_time": datetime.utcnow().isoformat()}
    assert _match_transaction_for_topup(tx_ok, topup, used) is True

    tx_wrong_amount = {"transaction_id": "TX-2", "amount": 50000,
                       "transaction_time": datetime.utcnow().isoformat()}
    assert _match_transaction_for_topup(tx_wrong_amount, topup, used) is False

    used.add("TX-1")
    assert _match_transaction_for_topup(tx_ok, topup, used) is False  # sudah diklaim
    print("[PASS] matcher nominal + anti klaim ganda")


# ---------------- Main ----------------
async def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add_all([
            WalletBalance(network="BASE", symbol="ETH", balance=10, address="0x" + "1" * 40),
            WalletBalance(network="SOLANA", symbol="SOL", balance=10, address="A" * 32),
            WalletBalance(network="TON", symbol="TON", balance=10, address="EQ" + "A" * 46),
        ])
        db.commit()

        # aktifkan mock
        tx_verifier.verify_deposit = fake_verify
        tx_verifier.get_recent_incoming = fake_recent_incoming
        payout_service.send_order_payout = fake_payout

        test_fee_engine()
        test_sender_factory()
        await test_swap_lifecycle(db)
        await test_autoscan(db)
        await test_sell(db)
        await test_buy_gopay(db)
        test_topup_matcher(db)
        print("\n" + "=" * 50)
        print("  ALL E2E ENGINE TESTS PASSED")
        print("=" * 50)
    finally:
        db.close()
    try:
        engine.dispose()
        if os.path.exists(_tmp_db):
            os.remove(_tmp_db)
    except PermissionError:
        pass  # Windows: file masih dipakai proses lain — tidak fatal


if __name__ == "__main__":
    asyncio.run(main())
