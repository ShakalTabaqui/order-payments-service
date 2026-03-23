"""Use-cases для работы с платежами по заказам (application слой)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.enums import OrderPaymentStatus, PaymentStatus, PaymentType
from app.domain.errors import ConflictError, NotFoundError, ValidationError
from app.infra.bank.client import BankClient
from app.infra.repositories import orders as order_repo
from app.infra.repositories import payments as payment_repo


def list_payments_by_order(db: Session, *, order_id: int):
    """Список платежей по заказу."""

    order = order_repo.get_order(db, order_id)
    if not order:
        raise NotFoundError("Заказ не найден")

    return payment_repo.list_payments_by_order(db, order_id)


def get_payment(db: Session, *, payment_id: int):
    """Получить платеж по идентификатору."""

    payment = payment_repo.get_payment(db, payment_id)
    if not payment:
        raise NotFoundError("Платёж не найден")
    return payment


def _recalc_order_status(db: Session, order_id: int) -> str:
    db.flush()

    paid_amount = payment_repo.sum_paid_amount(db, order_id)
    order = order_repo.get_order_for_update(db, order_id)
    if not order:
        raise NotFoundError("Заказ не найден")

    if paid_amount <= 0:
        status = OrderPaymentStatus.UNPAID.value
    elif paid_amount < order.total_amount:
        status = OrderPaymentStatus.PARTIALLY_PAID.value
    else:
        status = OrderPaymentStatus.PAID.value

    order.payment_status = status
    order.updated_at = datetime.utcnow()
    return status


def deposit_payment(
    db: Session,
    *,
    order_id: int,
    amount: Decimal,
    payment_type: str,
    bank_client: BankClient | None = None,
):
    """Создать платёж (депозит) по заказу."""

    if amount <= 0:
        raise ValidationError("Сумма платежа должна быть больше 0")

    order = order_repo.get_order_for_update(db, order_id)
    if not order:
        raise NotFoundError("Заказ не найден")

    reserved = payment_repo.sum_reserved_amount(db, order_id)
    if reserved + amount > order.total_amount:
        raise ValidationError("Сумма платежей превышает сумму заказа")

    if payment_type == PaymentType.CASH.value:
        payment = payment_repo.create_payment(
            db,
            order_id=order_id,
            payment_type=PaymentType.CASH.value,
            amount=amount,
            status=PaymentStatus.SUCCEEDED.value,
        )
        _recalc_order_status(db, order_id)
        return payment

    if payment_type == PaymentType.ACQUIRING.value:
        client = bank_client or BankClient()
        start = client.acquiring_start(order_id=order_id, amount=amount)
        payment = payment_repo.create_payment(
            db,
            order_id=order_id,
            payment_type=PaymentType.ACQUIRING.value,
            amount=amount,
            status=PaymentStatus.PENDING.value,
            bank_payment_id=start.bank_payment_id,
        )
        order.updated_at = datetime.utcnow()
        return payment

    raise ValidationError("Неизвестный тип платежа")


def refund_payment(db: Session, *, payment_id: int) -> None:
    """Выполнить возврат платежа."""

    payment = payment_repo.get_payment(db, payment_id)
    if not payment:
        raise NotFoundError("Платёж не найден")

    if payment.status == PaymentStatus.REFUNDED.value:
        raise ConflictError("Платёж уже возвращён")
    if payment.status != PaymentStatus.SUCCEEDED.value:
        raise ValidationError("Возврат возможен только для успешного платежа")

    order = order_repo.get_order_for_update(db, payment.order_id)
    if not order:
        raise NotFoundError("Заказ не найден")

    payment_repo.mark_refunded(payment)
    _recalc_order_status(db, order.id)


def sync_acquiring_payment(
    db: Session,
    *,
    payment_id: int,
    bank_client: BankClient | None = None,
):
    """Синхронизировать состояние эквайрингового платежа с банком."""

    payment = payment_repo.get_payment(db, payment_id)
    if not payment:
        raise NotFoundError("Платёж не найден")

    if payment.payment_type != PaymentType.ACQUIRING.value:
        raise ValidationError("Синхронизация доступна только для эквайринга")
    if not payment.bank_payment_id:
        raise ValidationError("Отсутствует bank_payment_id")
    if payment.status in [
        PaymentStatus.SUCCEEDED.value,
        PaymentStatus.REFUNDED.value,
        PaymentStatus.FAILED.value,
    ]:
        return payment

    client = bank_client or BankClient()
    check = client.acquiring_check(bank_payment_id=payment.bank_payment_id)

    payment_repo.update_bank_state(
        payment,
        bank_status=check.status,
        bank_paid_at=check.paid_at,
    )

    if check.status == "paid":
        payment_repo.mark_succeeded(payment)
        _recalc_order_status(db, payment.order_id)
    elif check.status == "failed":
        payment_repo.mark_failed(payment)

    return payment
