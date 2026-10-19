"""Motor de base de datos, fábrica de sesiones y creación de tablas."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.config import DATA_DIR, DATABASE_URL


def crear_motor(url: str = DATABASE_URL) -> Engine:
    """Crea un motor SQLAlchemy. En SQLite activa claves foráneas; en PostgreSQL
    (p. ej. ``postgresql+psycopg://...``) usa la configuración por defecto del driver."""
    es_sqlite = url.startswith("sqlite:///")
    if es_sqlite and ":memory:" not in url:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    motor = create_engine(url, connect_args={"check_same_thread": False} if es_sqlite else {})

    if es_sqlite:
        @event.listens_for(motor, "connect")
        def _activar_fk(conexion, _registro) -> None:  # noqa: ANN001
            cursor = conexion.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return motor


engine: Engine = crear_motor()
SesionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def crear_tablas(motor: Engine = engine) -> None:
    """Crea todas las tablas definidas en ``src.models`` si no existen."""
    from src import models  # noqa: F401  (registra los modelos)
    from src.models import Base

    Base.metadata.create_all(motor)


@contextmanager
def obtener_sesion() -> Iterator[Session]:
    """Entrega una sesión que hace *commit* al salir o *rollback* si hay error."""
    sesion = SesionLocal()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
