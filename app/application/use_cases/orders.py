"""Use-cases для работы с заказами (application слой)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.errors import NotFoundError
from app.infra.repositories import orders as order_repo


def list_orders(db: Session, *, limit: int = 100, offset: int = 0):
    """Вернуть список заказов."""

    return order_repo.list_orders(db, limit=limit, offset=offset)


def get_order(db: Session, order_id: int):
    """Получить заказ по идентификатору."""

    order = order_repo.get_order(db, order_id)
    if not order:
        raise NotFoundError("Заказ не найден")
    return order
