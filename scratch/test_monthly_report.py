"""
scratch/test_monthly_report.py — Test fitur laporan keuangan bulanan.
========================================================================
Menguji:
  1. get_completed_order_count: hanya order completed yang dihitung.
  2. build_monthly_report: agregasi order (buy/sell/swap) + topup SUCCESS
     untuk bulan berjalan; order non-completed & topup non-SUCCESS diabaikan.
  3. Guard anti-ganda: get_monthly_report terisi setelah disimpan.
DB SQLite sementara (tidak menyentuh p2p_bot.db).
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta

_tmp_db = os.path.join(tempfile.gettempdir(), "opencode", "report_test_bot.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal, engine, Base
from database.models import Order, TopupOrder, User
from database.crud import (
    get_completed_order_count,
    build_monthly_report,
    get_monthly_report,
)

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.utcnow()

    db.add(User(telegram_id=1)); db.commit()

    def mk_order(oid, otype, total, fee, status):
        db.add(Order(
            order_id=oid, telegram_id=1, order_type=otype,
            crypto_symbol="USDT", network="BSC", crypto_amount=1.0,
            price_per_unit=16000, nominal_idr=total, fee_idr=fee, total_idr=total,
            status=status, created_at=now - timedelta(days=5),
        ))

    # order completed: 2 buy, 1 sell, 1 swap
    mk_order("M1-BUY1", "buy",  500000, 8500, "completed")
    mk_order("M1-BUY2", "buy",  250000, 7000, "completed")
    mk_order("M1-SELL", "sell", 300000, 6500, "completed")
    mk_order("M1-SWAP", "swap", 400000, 9000, "completed")
    # order pending/paid/expired: tidak dihitung
    mk_order("M1-PEND", "buy",  999999, 1, "pending")
    mk_order("M1-EXP",  "buy",  888888, 1, "expired")
    db.commit()

    # topup: 2 SUCCESS + 1 PENDING (tidak dihitung)
    db.add_all([
        TopupOrder(topup_id="M1-TP1", telegram_id=1, amount_idr=100000, status="SUCCESS", created_at=now - timedelta(days=4)),
        TopupOrder(topup_id="M1-TP2", telegram_id=1, amount_idr=25000, status="SUCCESS", created_at=now - timedelta(days=2)),
        TopupOrder(topup_id="M1-TP3", telegram_id=1, amount_idr=50000, status="PENDING", created_at=now - timedelta(days=1)),
    ])
    db.commit()

    # --- 1. Total transaksi berhasil seumur hidup ---
    assert get_completed_order_count(db) == 4, f"count={get_completed_order_count(db)}"
    print("[PASS] get_completed_order_count = 4 (pending/expired diabaikan)")

    # --- 2. build_monthly_report bulan berjalan ---
    report = build_monthly_report(db, now.year, now.month)
    assert report.order_count == 4
    assert report.order_buy == 2 and report.order_sell == 1 and report.order_swap == 1
    assert report.volume_idr == 500000 + 250000 + 300000 + 400000
    assert report.fee_idr == 8500 + 7000 + 6500 + 9000
    assert report.topup_count == 2
    assert report.topup_idr == 125000
    assert report.total_idr == report.volume_idr + report.fee_idr + report.topup_idr
    print(f"[PASS] build_monthly_report: {report.order_count} order, vol {report.volume_idr}, fee {report.fee_idr}, topup {report.topup_idr}")

    # --- 3. Guard anti-ganda: simpan lalu cek get_monthly_report ---
    assert get_monthly_report(db, report.period) is None
    db.add(report); db.commit()
    assert get_monthly_report(db, report.period) is not None
    print(f"[PASS] guard anti-ganda: period {report.period} terdeteksi setelah disimpan")

    # --- 4. Report bulan lain harus kosong (masa depan) ---
    future = datetime.utcnow() + timedelta(days=60)
    empty = build_monthly_report(db, future.year, future.month)
    assert empty.order_count == 0 and empty.topup_count == 0
    print("[PASS] bulan tanpa transaksi -> 0")

    print("=" * 50)
    print("  MONTHLY REPORT TESTS PASSED")
    print("=" * 50)

    db.close()
    engine.dispose()
    try:
        if os.path.exists(_tmp_db):
            os.remove(_tmp_db)
    except PermissionError:
        pass


if __name__ == "__main__":
    main()
