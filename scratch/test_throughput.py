"""
scratch/test_throughput.py — Benchmark job polling vs 100 order pending.
==========================================================================
Menguji:
  1. `_job_check_pending_buy_payments` memproses 100 order pending dalam
     satu tick dengan verifikasi massal /transactions (bukan 100x check-payment).
  2. 50 order yang terbayar di-finalize paralel; payout tepat 50x.
  3. Durasi tick tetap rendah (bottleneck lama: loop sequential).
DB SQLite sementara.
"""

import os
import sys
import time
import asyncio
import tempfile
from datetime import datetime, timedelta

_tmp_db = os.path.join(tempfile.gettempdir(), "opencode", "throughput_test_bot.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal, engine, Base
from database.models import Order, User

PAYOUT_CALLS = []


def seed(db, n=100, n_paid=50):
    for i in range(n):
        user = User(telegram_id=900000 + i)
        db.add(user)
    db.commit()
    for i in range(n):
        code = (i % 99) + 1
        order = Order(
            order_id=f"THR-{i:04d}", telegram_id=900000 + i, order_type="buy",
            crypto_symbol="USDT", network="BSC", crypto_amount=1.0,
            price_per_unit=16000, nominal_idr=16000, fee_idr=1000,
            total_idr=17000 + code,
            unique_code=code, buyer_wallet="0xBuyer" + "1" * 40,
            payment_method="GOPAY_QRIS", status="pending",
            created_at=datetime.utcnow() - timedelta(minutes=5),
        )
        db.add(order)
    db.commit()


def fake_txns_for(order_count):
    # 50 transaksi lunas (nominal cocok 50 order pertama), sisanya acak
    txns = []
    for i in range(order_count):
        code = (i % 99) + 1
        txns.append({
            "transaction_id": f"TX-{i:05d}",
            "amount": 17000 + code,
            "transaction_time": datetime.utcnow().isoformat(),
        })
    for i in range(100):
        txns.append({
            "transaction_id": f"TX-EXTRA-{i:05d}",
            "amount": 100000 + i,
            "transaction_time": datetime.utcnow().isoformat(),
        })
    return txns


async def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed(db, 100, 50)

    import services.gopay_service as gopay_service
    import bot.handlers.buy as buy_mod

    async def fake_recent(page_size=100):
        return fake_txns_for(50)

    gopay_service.gopay_service.get_recent_transactions = fake_recent
    gopay_service.gopay_service.check_payment = lambda amount, trx_id: {"paid": False}

    async def fake_finalize(order_id, bot=None, **kwargs):
        PAYOUT_CALLS.append(order_id)
        s = SessionLocal()
        try:
            o = s.query(Order).filter(Order.order_id == order_id).first()
            if o:
                o.status = "completed"
                o.payout_tx_hash = "0xTHR"
                o.completed_at = datetime.utcnow()
                s.commit()
        finally:
            s.close()

    buy_mod._run_finalize_background = fake_finalize

    from main import _job_check_pending_buy_payments

    start = time.perf_counter()
    await _job_check_pending_buy_payments()
    elapsed = time.perf_counter() - start

    completed = db.query(Order).filter(Order.status == "completed").count()
    still_pending = db.query(Order).filter(Order.status == "pending").count()

    assert completed == 50, f"completed={completed}"
    assert still_pending == 50, f"pending={still_pending}"
    assert len(PAYOUT_CALLS) == 50, f"payout={len(PAYOUT_CALLS)}"
    assert elapsed < 5.0, f"satu tick terlalu lama: {elapsed:.2f}s"
    print(f"[PASS] 100 order dalam satu tick: {elapsed:.2f}s, 50 finalized, 50 pending")
    print("=" * 50)
    print("  THROUGHPUT TEST PASSED")
    print("=" * 50)

    db.close()
    engine.dispose()
    try:
        if os.path.exists(_tmp_db):
            os.remove(_tmp_db)
    except PermissionError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
