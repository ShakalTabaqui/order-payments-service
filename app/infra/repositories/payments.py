"""Репозиторий платежей (infra): создание и выборки."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infra.db.models import Payment


def list_payments_by_order(db: Session, order_id: int) -> list[Payment]:
    """Список платежей по заказу."""

    stmt = (
        select(Payment)
        .where(Payment.order_id == order_id)
        .order_by(Payment.id)
    )
    return db.execute(stmt).scalars().all()


def get_payment(db: Session, payment_id: int) -> Payment | None:
    """Получить платёж по идентификатору."""

    stmt = select(Payment).where(Payment.id == payment_id)
    return db.execute(stmt).scalars().first()


def create_payment(
    db: Session,
    *,
    order_id: int,
    payment_type: str,
    amount: Decimal,
    status: str,
    bank_payment_id: str | None = None,
) -> Payment:
    """Создать платёж."""

    payment = Payment(
        order_id=order_id,
        payment_type=payment_type,
        amount=amount,
        status=status,
        bank_payment_id=bank_payment_id,
    )
    db.add(payment)
    db.flush()
    return payment


def mark_refunded(payment: Payment) -> None:
    """Пометить платёж как возвращённый."""

    payment.status = "refunded"
    payment.refunded_at = datetime.utcnow()
    payment.updated_at = datetime.utcnow()


def mark_succeeded(payment: Payment) -> None:
    """Пометить платёж как успешный (оплачен)."""

    payment.status = "succeeded"
    payment.updated_at = datetime.utcnow()


def mark_failed(payment: Payment) -> None:
    """Пометить платёж как неуспешный."""

    payment.status = "failed"
    payment.updated_at = datetime.utcnow()


def update_bank_state(
    payment: Payment,
    *,
    bank_status: str,
    bank_paid_at: datetime | None,
) -> None:
    """Обновить состояние платежа по данным банка."""

    payment.bank_status = bank_status
    payment.bank_paid_at = bank_paid_at
    payment.updated_at = datetime.utcnow()


def sum_reserved_amount(db: Session, order_id: int) -> Decimal:
    """Сумма платежей, учитываемых в лимите суммы заказа.

    Включает pending и succeeded. Refunded и failed не учитываются.
    """

    stmt = select(
        func.coalesce(func.sum(Payment.amount), 0),
    ).where(
        Payment.order_id == order_id,
        Payment.status.in_(["pending", "succeeded"]),
    )
    return db.execute(stmt).scalar_one()


def sum_paid_amount(db: Session, order_id: int) -> Decimal:
    """Сумма оплаченных денег по заказу.

    Учитывает только платежи со статусом succeeded.
    """

    stmt = select(
        func.coalesce(func.sum(Payment.amount), 0),
    ).where(
        Payment.order_id == order_id,
        Payment.status == "succeeded",
    )
    return db.execute(stmt).scalar_one()
