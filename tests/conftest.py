"""Fixtures compartidas: base de datos en memoria con datos mínimos."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.auth import hash_contrasena
from src.db import crear_motor, crear_tablas
from src.models import Producto, Tienda, Usuario


@pytest.fixture()
def sesion() -> Iterator[Session]:
    """Sesión sobre SQLite en memoria con una tienda, un producto y dos usuarios."""
    motor = crear_motor("sqlite:///:memory:")
    crear_tablas(motor)
    s = sessionmaker(bind=motor, expire_on_commit=False)()
    s.add_all([
        Tienda(id=1, nombre="Tienda Prado", ciudad="La Paz", tipo="tienda"),
        Producto(id=1, codigo_modelo="MAN-DEP-001", nombre="Zapatilla Runner", categoria="Deportivo",
                 codigo_sa6=640411, talla="40", color="Negro", precio_venta_bs=389.0, costo_bs=210.0),
        Usuario(id=1, nombre="Administrador", usuario="admin", hash_contrasena=hash_contrasena("manaco2026"),
                rol="administrador"),
        Usuario(id=2, nombre="Encargado", usuario="encargado", hash_contrasena=hash_contrasena("clave123"),
                rol="encargado"),
    ])
    s.flush()
    yield s
    s.close()
    motor.dispose()


@pytest.fixture()
def hoy() -> date:
    return date(2026, 10, 16)
