"""Ручки для операций с платежами."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.mappers import payment_to_out
from app.api.schemas import PaymentOut
from app.application.use_cases import payments as payments_uc
from app.domain.errors import (
    ConflictError,
    DomainError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from app.infra.db.session import get_db

router = APIRouter(prefix="/payments", tags=["Платежи"])


@router.get(
    "/{payment_id}",
    response_model=PaymentOut,
    summary="Платёж по идентификатору",
    description="Возвращает данные по платежу.",
)
def get_payment(payment_id: int, db: Session = Depends(get_db)) -> PaymentOut:
    """Получить платеж по `payment_id`."""

    try:
        payment = payments_uc.get_payment(db, payment_id=payment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return payment_to_out(payment)


@router.post(
    "/{payment_id}/refund",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Возврат платежа",
    description="Выполняет возврат платежа и пересчитывает статус заказа.",
)
def refund(payment_id: int, db: Session = Depends(get_db)) -> Response:
    """Выполнить возврат платежа."""

    try:
        payments_uc.refund_payment(db, payment_id=payment_id)
        db.commit()
    except ConflictError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{payment_id}/sync",
    response_model=PaymentOut,
    summary="Синхронизация эквайринга",
    description=(
        "Запрашивает состояние платежа в банке и обновляет его в системе."
    ),
)
def sync(payment_id: int, db: Session = Depends(get_db)) -> PaymentOut:
    """Синхронизировать эквайринговый платеж."""

    try:
        payment = payments_uc.sync_acquiring_payment(db, payment_id=payment_id)
        db.commit()
    except ValidationError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DomainError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return payment_to_out(payment)
