"""Мапперы API: преобразование ORM-моделей в схемы ответов."""

from __future__ import annotations

from app.api.schemas import OrderOut, PaymentOut


def order_to_out(order) -> OrderOut:
    """Преобразовать ORM-модель заказа в схему ответа."""

    return OrderOut.model_validate(order)


def payment_to_out(payment) -> PaymentOut:
    """Преобразовать ORM-модель платежа в схему ответа."""

    return PaymentOut.model_validate(payment)
