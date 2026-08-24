"""Focused tests for fee boundaries, wallet validation, and inventory claims."""

import os
import sys
import tempfile
from decimal import Decimal

_tmp_db = os.path.join(tempfile.gettempdir(), "opencode", "fee_inventory_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
if os.path.exists(_tmp_db):
    os.remove(_tmp_db)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import Base, SessionLocal, engine
from database.crud import (
    get_available_inventory,
    release_order_inventory,
    reserve_order_inventory,
)
from database.models import WalletBalance
from services.fee_service import calculate_fee_idr
from bot.utils.validator import validate_wallet_address


def main():
    assert calculate_fee_idr(1_010_000, "ALTCOIN") == 18_000
    assert calculate_fee_idr(1_010_001, "ALTCOIN") == 20_201
    assert calculate_fee_idr(1_575_000, "ALTCOIN") == 31_500
    assert calculate_fee_idr(1_015_000, "USD") == 14_000
    assert calculate_fee_idr(1_205_000, "USD") == 18_075
    assert calculate_fee_idr(1_010_000, "CONVERT") == 17_000
    assert calculate_fee_idr(1_575_000, "CONVERT") == 31_500
    print("[PASS] fee tiers, caps, percentage ceiling")

    assert validate_wallet_address("0x" + "a" * 40, "ROBINHOOD")
    assert validate_wallet_address("0x" + "a" * 64, "SUI")
    assert validate_wallet_address("0x1", "APTOS")
    assert validate_wallet_address("0:" + "a" * 64, "TON")
    assert not validate_wallet_address("not-a-ton-wallet", "TON")
    print("[PASS] EVM/TON/SUI/APTOS validators")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(WalletBalance(
        network="SOLANA", symbol="USDC", balance=6,
        reserved_balance=0, address="A" * 32,
    ))
    db.commit()
    assert reserve_order_inventory(db, "ORD-1", "SOLANA", "USDC", Decimal("5"))
    assert get_available_inventory(db, "SOLANA", "USDC") == Decimal("1")
    assert reserve_order_inventory(db, "ORD-1", "SOLANA", "USDC", Decimal("5"))
    assert not reserve_order_inventory(db, "ORD-2", "SOLANA", "USDC", Decimal("2"))
    assert release_order_inventory(db, "ORD-1")
    assert get_available_inventory(db, "SOLANA", "USDC") == Decimal("6")
    print("[PASS] inventory reservation prevents oversell and releases cleanly")

    db.close()
    engine.dispose()
    try:
        if os.path.exists(_tmp_db):
            os.remove(_tmp_db)
    except PermissionError:
        pass

    print("ALL FEE/INVENTORY/VALIDATOR TESTS PASSED")


if __name__ == "__main__":
    main()
