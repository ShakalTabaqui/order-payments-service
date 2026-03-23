"""Доменные перечисления для сервиса платежей."""

from __future__ import annotations

from enum import StrEnum


class OrderPaymentStatus(StrEnum):
    """Статус оплаты заказа."""

    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class PaymentType(StrEnum):
    """Тип платежа."""

    CASH = "cash"
    ACQUIRING = "acquiring"


class PaymentStatus(StrEnum):
    """Статус платежа в системе."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
