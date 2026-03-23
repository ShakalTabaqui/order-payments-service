"""Репозиторий заказов (infra): чтение и блокировка на обновление."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.infra.db.models import Order


def list_orders(
    db: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[Order]:
    """Вернуть список заказов."""

    stmt: Select[tuple[Order]] = (
        select(Order)
        .order_by(Order.id)
        .limit(limit)
        .offset(offset)
    )
    return db.execute(stmt).scalars().all()


def get_order(db: Session, order_id: int) -> Order | None:
    """Получить заказ по идентификатору."""

    stmt = select(Order).where(Order.id == order_id)
    return db.execute(stmt).scalars().first()


def get_order_for_update(db: Session, order_id: int) -> Order | None:
    """Получить заказ с блокировкой строки (SELECT ... FOR UPDATE)."""

    stmt: Select[tuple[Order]] = (
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
    )
    return db.execute(stmt).scalars().first()
