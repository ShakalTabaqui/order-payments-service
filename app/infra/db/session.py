"""SQLAlchemy engine/session и зависимость FastAPI для доступа к БД."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infra.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Открыть сессию БД на время запроса и корректно закрыть."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
