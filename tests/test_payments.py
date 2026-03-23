"""Тесты бизнес-логики сервиса платежей."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.use_cases import payments as payments_uc
from app.domain.errors import ValidationError
from app.infra.bank.client import BankCheckResult, BankStartResult
from app.infra.db.models import Base, Order


@pytest.fixture()
def db() -> Session:
    """Сессия SQLAlchemy на SQLite in-memory для тестов."""

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


class DummyBankClient:
    """Тестовый клиент банка (заглушка)."""

    def __init__(self, *, status: str = "paid") -> None:
        self._status = status

    def acquiring_start(
        self,
        *,
        order_id: int,
        amount: Decimal,
    ) -> BankStartResult:
        return BankStartResult(bank_payment_id=f"bank-{order_id}-1")

    def acquiring_check(self, *, bank_payment_id: str) -> BankCheckResult:
        return BankCheckResult(
            bank_payment_id=bank_payment_id,
            amount=Decimal("10.00"),
            status=self._status,
            paid_at=datetime.utcnow() if self._status == "paid" else None,
        )


def test_cash_deposit_and_refund_updates_order_status(db: Session) -> None:
    """Наличный депозит и возврат согласованно меняют статус заказа."""

    order = Order(total_amount=Decimal("200.00"), payment_status="unpaid")
    db.add(order)
    db.commit()

    p1 = payments_uc.deposit_payment(
        db,
        order_id=order.id,
        amount=Decimal("100.00"),
        payment_type="cash",
    )
    db.commit()
    assert db.get(Order, order.id).payment_status == "partially_paid"

    payments_uc.deposit_payment(
        db,
        order_id=order.id,
        amount=Decimal("100.00"),
        payment_type="cash",
    )
    db.commit()
    assert db.get(Order, order.id).payment_status == "paid"

    payments_uc.refund_payment(db, payment_id=p1.id)
    db.commit()
    assert db.get(Order, order.id).payment_status == "partially_paid"


def test_overpay_is_rejected(db: Session) -> None:
    """Нельзя оплатить заказ на сумму больше его total_amount."""

    order = Order(total_amount=Decimal("200.00"), payment_status="unpaid")
    db.add(order)
    db.commit()

    payments_uc.deposit_payment(
        db,
        order_id=order.id,
        amount=Decimal("199.00"),
        payment_type="cash",
    )
    db.commit()

    with pytest.raises(ValidationError):
        payments_uc.deposit_payment(
            db,
            order_id=order.id,
            amount=Decimal("2.00"),
            payment_type="cash",
        )


def test_acquiring_sync_can_mark_payment_as_paid(db: Session) -> None:
    """Синхронизация эквайринга обновляет статус платежа и заказа."""

    order = Order(total_amount=Decimal("10.00"), payment_status="unpaid")
    db.add(order)
    db.commit()

    bank = DummyBankClient(status="paid")
    p = payments_uc.deposit_payment(
        db,
        order_id=order.id,
        amount=Decimal("10.00"),
        payment_type="acquiring",
        bank_client=bank,
    )
    db.commit()

    payments_uc.sync_acquiring_payment(db, payment_id=p.id, bank_client=bank)
    db.commit()

    assert db.get(Order, order.id).payment_status == "paid"
