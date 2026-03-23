"""Заполнение БД тестовыми данными (seed) для сервиса платежей.

Скрипт идемпотентный: если в таблице `orders` уже есть записи, то seed
пропускается.
"""

from __future__ import annotations

import os
import time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.infra.db.models import Order
from app.infra.db.session import SessionLocal


def wait_for_db(timeout_s: int = 30) -> None:
    """Подождать, пока БД станет доступной для подключения."""

    deadline = time.time() + timeout_s
    while True:
        try:
            with SessionLocal() as db:
                db.execute(select(1))
            return
        except OperationalError:
            if time.time() > deadline:
                raise
            time.sleep(1)


def seed() -> None:
    """Применить seed данных (заказы)."""

    wait_for_db(timeout_s=int(os.environ.get("DB_WAIT_TIMEOUT_S", "60")))
    with SessionLocal() as db:
        existing = db.execute(select(Order.id).limit(1)).scalar_one_or_none()
        if existing:
            return

        orders = [
            Order(total_amount=Decimal("1000.00"), payment_status="unpaid"),
            Order(total_amount=Decimal("2500.00"), payment_status="unpaid"),
        ]
        db.add_all(orders)
        db.commit()


if __name__ == "__main__":
    seed()
