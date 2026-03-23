"""Доменные ошибки и исключения приложения."""

from __future__ import annotations


class DomainError(Exception):
    """Базовая ошибка доменного уровня."""


class NotFoundError(DomainError):
    """Сущность не найдена."""


class ValidationError(DomainError):
    """Ошибка валидации бизнес-правил."""


class ConflictError(DomainError):
    """Конфликт состояния (например, повторная операция)."""


class ExternalServiceError(DomainError):
    """Ошибка внешней системы (например, API банка)."""
