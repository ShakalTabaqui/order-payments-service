"""Ручки для работы с заказами и платежами по заказу."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.mappers import order_to_out, payment_to_out
from app.api.schemas import OrderOut, PaymentDepositIn, PaymentOut
from app.application.use_cases import orders as orders_uc
from app.application.use_cases import payments as payments_uc
from app.domain.errors import (
    DomainError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from app.infra.db.session import get_db

router = APIRouter(prefix="/orders", tags=["Заказы"])


@router.get(
    "",
    response_model=list[OrderOut],
    summary="Список заказов",
    description="Возвращает список существующих заказов.",
)
def list_orders(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Максимальное количество записей.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Смещение (для пагинации).",
    ),
    db: Session = Depends(get_db),
) -> list[OrderOut]:
    """Получить список заказов."""

    orders = orders_uc.list_orders(db, limit=limit, offset=offset)
    return [order_to_out(o) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    summary="Заказ по идентификатору",
    description="Возвращает данные по заказу.",
)
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderOut:
    """Получить заказ по `order_id`."""

    try:
        order = orders_uc.get_order(db, order_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return order_to_out(order)


@router.get(
    "/{order_id}/payments",
    response_model=list[PaymentOut],
    summary="Платежи по заказу",
    description="Возвращает список платежей по заказу.",
)
def list_payments(
    order_id: int,
    db: Session = Depends(get_db),
) -> list[PaymentOut]:
    """Получить платежи по заказу."""

    try:
        payments = payments_uc.list_payments_by_order(db, order_id=order_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [payment_to_out(p) for p in payments]


@router.post(
    "/{order_id}/payments",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать платеж (депозит)",
    description=(
        "Создаёт платеж по заказу. Для эквайринга вызывает API банка."
    ),
)
def create_payment(
    order_id: int,
    payload: PaymentDepositIn,
    db: Session = Depends(get_db),
) -> PaymentOut:
    """Создать платеж (депозит) по заказу."""

    try:
        payment = payments_uc.deposit_payment(
            db,
            order_id=order_id,
            amount=payload.amount,
            payment_type=payload.payment_type,
        )
        db.commit()
    except ValidationError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except DomainError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return payment_to_out(payment)
