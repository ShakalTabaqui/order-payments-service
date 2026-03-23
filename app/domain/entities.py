"""Доменные сущности (минимальные структуры)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.enums import OrderPaymentStatus, PaymentStatus, PaymentType


@dataclass(frozen=True, slots=True)
class Order:
    """Заказ."""

    id: int
    total_amount: Decimal
    payment_status: OrderPaymentStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Payment:
    """Платёж по заказу."""

    id: int
    order_id: int
    payment_type: PaymentType
    status: PaymentStatus
    amount: Decimal
    bank_payment_id: str | None
    bank_status: str | None
    bank_paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
    refunded_at: datetime | None
