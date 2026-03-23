"""Pydantic-схемы API для сервиса платежей."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderOut(BaseModel):
    """Заказ (ответ API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Идентификатор заказа.")
    total_amount: Decimal = Field(..., description="Сумма заказа.")
    payment_status: str = Field(..., description="Статус оплаты заказа.")
    created_at: datetime = Field(..., description="Дата и время создания.")
    updated_at: datetime = Field(..., description="Дата и время обновления.")


class PaymentOut(BaseModel):
    """Платёж (ответ API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Идентификатор платежа.")
    order_id: int = Field(..., description="Идентификатор заказа.")
    payment_type: str = Field(..., description="Тип платежа (cash/acquiring).")
    status: str = Field(
        ...,
        description="Статус платежа (pending/succeeded/failed/refunded).",
    )
    amount: Decimal = Field(..., description="Сумма платежа.")

    bank_payment_id: str | None = Field(
        default=None,
        description="Уникальный идентификатор платежа в банке.",
    )
    bank_status: str | None = Field(
        default=None,
        description="Статус платежа по данным банка.",
    )
    bank_paid_at: datetime | None = Field(
        default=None,
        description="Дата и время оплаты по данным банка.",
    )

    created_at: datetime = Field(..., description="Дата и время создания.")
    updated_at: datetime = Field(..., description="Дата и время обновления.")
    refunded_at: datetime | None = Field(
        default=None,
        description="Дата и время возврата (если был выполнен).",
    )


class PaymentDepositIn(BaseModel):
    """Входные данные для создания платежа (депозит)."""

    amount: Decimal = Field(..., gt=0, description="Сумма платежа (> 0).")
    payment_type: str = Field(
        ...,
        description="Тип платежа: cash (наличные) или acquiring (эквайринг).",
    )
