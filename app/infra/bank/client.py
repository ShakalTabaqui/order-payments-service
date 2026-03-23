"""HTTP-клиент для внешнего API банка.

API банка является внешней системой: запросы выполняются с таймаутом и
оборачиваются в исключения доменного уровня.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import httpx

from app.domain.errors import ExternalServiceError
from app.infra.settings import settings


@dataclass(frozen=True, slots=True)
class BankStartResult:
    """Результат запроса `acquiring_start`."""

    bank_payment_id: str


@dataclass(frozen=True, slots=True)
class BankCheckResult:
    """Результат запроса `acquiring_check`."""

    bank_payment_id: str
    amount: Decimal
    status: str
    paid_at: datetime | None


class BankClient:
    """Клиент для ресурсов `acquiring_start` и `acquiring_check`."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self._base_url = base_url or settings.bank_api_base_url
        self._timeout_s = (
            timeout_s if timeout_s is not None else settings.bank_api_timeout_s
        )

    def acquiring_start(
        self,
        *,
        order_id: int,
        amount: Decimal,
    ) -> BankStartResult:
        """Создать платеж в банке (эквайринг)."""

        url = f"{self._base_url.rstrip('/')}/acquiring_start"
        payload = {
            "order_id": order_id,
            "amount": str(amount),
        }
        try:
            with httpx.Client(timeout=self._timeout_s) as client:
                resp = client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Ошибка связи с API банка") from exc

        if resp.status_code >= 500:
            raise ExternalServiceError("API банка недоступно")

        data = resp.json()
        bank_payment_id = data.get("bank_payment_id")
        if not bank_payment_id:
            error = data.get("error") or "Неизвестная ошибка банка"
            raise ExternalServiceError(str(error))

        return BankStartResult(bank_payment_id=str(bank_payment_id))

    def acquiring_check(self, *, bank_payment_id: str) -> BankCheckResult:
        """Проверить состояние платежа в банке."""

        url = f"{self._base_url.rstrip('/')}/acquiring_check"
        payload = {"bank_payment_id": bank_payment_id}
        try:
            with httpx.Client(timeout=self._timeout_s) as client:
                resp = client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Ошибка связи с API банка") from exc

        if resp.status_code == 404:
            raise ExternalServiceError("Платеж не найден")
        if resp.status_code >= 500:
            raise ExternalServiceError("API банка недоступно")

        data = resp.json()
        paid_at_raw = data.get("paid_at")
        paid_at = None
        if paid_at_raw:
            try:
                paid_at = datetime.fromisoformat(paid_at_raw)
            except ValueError:
                paid_at = None

        return BankCheckResult(
            bank_payment_id=str(data.get("bank_payment_id", bank_payment_id)),
            amount=Decimal(str(data.get("amount", "0"))),
            status=str(data.get("status", "unknown")),
            paid_at=paid_at,
        )
