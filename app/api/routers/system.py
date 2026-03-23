"""Системные (технические) ручки сервиса."""

from fastapi import APIRouter

router = APIRouter(tags=["Система"])


@router.get(
    "/health",
    summary="Проверка работоспособности",
    description="Возвращает статус сервиса.",
)
def health() -> dict:
    """Проверка готовности сервиса."""

    return {"status": "ok"}
