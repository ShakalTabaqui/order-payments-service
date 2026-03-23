"""Точка входа FastAPI приложения (composition root)."""

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html

from app.api.routers import orders, payments, system

app = FastAPI(
    title='REST API "Платежи по заказу"',
    docs_url="/docs",
    redoc_url=None,
    version="1.0.0",
    description=(
        "Сервис работы с платежами по заказу. "
        "Поддерживает депозиты и возвраты, а также интеграцию с API банка "
        "для эквайринга."
    ),
)

app.include_router(system.router)
app.include_router(orders.router)
app.include_router(payments.router)


@app.get("/redoc", include_in_schema=False)
async def redoc_html(request: Request):
    """Отдаёт ReDoc.

    Вынесен на отдельный путь вместо стандартного `/redoc`.
    """

    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_js_url=(
            "https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"
        ),
    )
