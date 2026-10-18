"""Crea las tablas, carga el Excel de comercio exterior y el usuario administrador.

Uso: ``python scripts/init_db.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # símbolos ✔ en consolas Windows

from sqlalchemy import select  # noqa: E402

from src.auth import crear_usuario  # noqa: E402
from src.config import (  # noqa: E402
    ADMIN_CONTRASENA, ADMIN_USUARIO, EXCEL_PATH, FOTOS_DIR, MODELOS_DIR, ROL_ADMIN,
)
from src.db import crear_tablas, obtener_sesion  # noqa: E402
from src.models import Usuario  # noqa: E402
from src.services.etl import cargar_excel_en_db  # noqa: E402


def main() -> None:
    """Inicializa la base de datos de Manaco Data."""
    FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    crear_tablas()
    print("✔ Tablas creadas.")

    with obtener_sesion() as sesion:
        if EXCEL_PATH.exists():
            resultado = cargar_excel_en_db(sesion)
            print(f"✔ Excel cargado: {resultado.filas_originales} filas → "
                  f"{resultado.filas_validas} válidas, {resultado.filas_descartadas} descartadas.")
        else:
            print(f"⚠ No se encontró el Excel en {EXCEL_PATH}; el tablero quedará vacío.")

        if sesion.scalar(select(Usuario).where(Usuario.usuario == ADMIN_USUARIO)) is None:
            crear_usuario(sesion, "Administrador", ADMIN_USUARIO, ADMIN_CONTRASENA, ROL_ADMIN)
            print(f"✔ Usuario '{ADMIN_USUARIO}' creado (contraseña: {ADMIN_CONTRASENA}). Cámbiela después.")
        else:
            print(f"• El usuario '{ADMIN_USUARIO}' ya existía.")


if __name__ == "__main__":
    main()
