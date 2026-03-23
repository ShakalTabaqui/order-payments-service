# Схема БД

База данных: PostgreSQL.

## Таблица `orders`

- `id` (PK, int) — идентификатор заказа
- `total_amount` (numeric(12,2), not null) — сумма заказа
- `payment_status` (varchar(32), not null) — статус оплаты заказа:
  - `unpaid` — не оплачен
  - `partially_paid` — частично оплачен
  - `paid` — оплачен
- `created_at` (timestamptz, not null) — дата создания
- `updated_at` (timestamptz, not null) — дата обновления

## Таблица `payments`

- `id` (PK, int) — идентификатор платежа
- `order_id` (FK -> orders.id, on delete cascade, not null) — заказ
- `payment_type` (varchar(32), not null) — тип платежа:
  - `cash` — наличные
  - `acquiring` — эквайринг
- `status` (varchar(32), not null) — статус платежа:
  - `pending` — ожидает подтверждения банка
  - `succeeded` — успешно оплачен
  - `failed` — неуспешный
  - `refunded` — возвращён
- `amount` (numeric(12,2), not null) — сумма платежа
- `bank_payment_id` (varchar(128), unique, null) — ID платежа в банке
- `bank_status` (varchar(64), null) — статус по данным банка
- `bank_paid_at` (timestamptz, null) — дата/время оплаты по данным банка
- `created_at` (timestamptz, not null) — дата создания
- `updated_at` (timestamptz, not null) — дата обновления
- `refunded_at` (timestamptz, null) — дата/время возврата

## Бизнес-ограничения

- Сумма всех платежей по заказу (pending + succeeded) не может превышать сумму
  заказа (`total_amount`). Проверяется на уровне приложения при создании платежа.

