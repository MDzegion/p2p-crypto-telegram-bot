"""
scratch/test_claims.py — Test atomic claim (anti double-payout / double-credit).
=================================================================================
Menguji:
  1. claim_order_paid: dua session claim order sama -> hanya 1 yang menang.
  2. claim_topup_success: dua session claim topup sama -> hanya 1 yang menang.
  3. get_gopay_resume_orders: order 'paid' tanpa payout_tx_hash terambil;
     yang sudah punya hash tidak.
DB SQLite sementara (tidak menyentuh p2p_bot.db).
"""

import os
import sys
import tempfile

_tmp_db = os.path.join(tempfile.gettempdir(), "opencode", "claim_test_bot.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal, engine, Base
from database.models import Order, TopupOrder, WalletBalance
from database.crud import (
    claim_order_paid,
    claim_topup_success,
    get_gopay_resume_orders,
    update_order_status,
)

def main():
    Base.metadata.create_all(bind=engine)

    db1 = SessionLocal()
    db2 = SessionLocal()
    db1.add(WalletBalance(
        network="SOLANA", symbol="SOL", balance=10,
        reserved_balance=0, address="A" * 32,
    ))
    db1.commit()

    # --- 1. Race claim order ---
    order = Order(
        order_id="RACE-ORD-1", telegram_id=999001, order_type="buy",
        crypto_symbol="USDT", network="BSC", crypto_amount=1.0,
        price_per_unit=16000, nominal_idr=16000, fee_idr=1000, total_idr=17000,
        payment_method="GOPAY_QRIS", status="pending",
    )
    db1.add(order); db1.commit()

    winner1 = claim_order_paid(db1, "RACE-ORD-1")
    loser = claim_order_paid(db2, "RACE-ORD-1")
    assert winner1 is True, "session 1 harus menang claim"
    assert loser is False, "session 2 harus kalah claim (sudah paid)"
    db1.refresh(order)
    assert order.status == "paid"
    print("[PASS] race claim order: 1 pemenang, tidak ada double-claim")

    # --- 2. Resume list: paid tanpa hash terambil; dengan hash tidak ---
    resume = get_gopay_resume_orders(db1)
    assert any(o.order_id == "RACE-ORD-1" for o in resume), "paid tanpa hash harus di-resume"
    update_order_status(db1, "RACE-ORD-1", "paid", payout_tx_hash="0xabc", completed_at=None)
    resume2 = get_gopay_resume_orders(db1)
    assert not any(o.order_id == "RACE-ORD-1" for o in resume2), "punya hash tidak boleh di-resume"
    print("[PASS] resume list hanya order paid tanpa payout_tx_hash")

    # --- 3. Race claim topup ---
    topup = TopupOrder(topup_id="RACE-TP-1", telegram_id=999002, amount_idr=25000, status="PENDING")
    db1.add(topup); db1.commit()

    t_winner = claim_topup_success(db1, "RACE-TP-1")
    t_loser = claim_topup_success(db2, "RACE-TP-1")
    assert t_winner is True
    assert t_loser is False
    db1.refresh(topup)
    assert topup.status == "SUCCESS"
    print("[PASS] race claim topup: 1 pemenang, tidak ada double-credit")

    # --- 4. Finalize ganda pada order yang sama (simulasi job + callback) ---
    order2 = Order(
        order_id="RACE-ORD-2", telegram_id=999003, order_type="buy",
        crypto_symbol="SOL", network="SOLANA", crypto_amount=2.0,
        price_per_unit=800000, nominal_idr=1600000, fee_idr=8500, total_idr=1608500,
        payment_method="GOPAY_QRIS", status="pending",
    )
    db1.add(order2); db1.commit()

    from bot.handlers.buy import finalize_gopay_buy_payment
    import services.payout_service as payout_service
    payout_service.send_order_payout = lambda order: None  # placeholder, diganti async
    calls = []

    async def fake_payout(order):
        calls.append(order.order_id)
        await asyncio.sleep(0.01)
        return {"success": True, "tx_hash": "0xRACE", "explorer_url": "", "error_message": ""}

    payout_service.send_order_payout = fake_payout

    import asyncio

    async def run_race():
        order2_other_session = db2.query(Order).filter(Order.order_id == "RACE-ORD-2").first()
        await asyncio.gather(
            finalize_gopay_buy_payment(db1, order2),
            finalize_gopay_buy_payment(db2, order2_other_session),
        )
        return

    asyncio.run(run_race())
    db1.refresh(order2)
    assert order2.status == "completed"
    assert calls.count("RACE-ORD-2") == 1, f"payout harus 1x, dapat {len(calls)}"
    print("[PASS] finalize ganda (job + callback): payout tetap 1x")

    print("=" * 50)
    print("  ALL CLAIM RACE TESTS PASSED")
    print("=" * 50)

    db1.close(); db2.close()
    engine.dispose()
    try:
        if os.path.exists(_tmp_db):
            os.remove(_tmp_db)
    except PermissionError:
        pass


if __name__ == "__main__":
    main()
