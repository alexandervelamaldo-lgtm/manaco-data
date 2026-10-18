"""Autenticación, roles y control de acceso a las páginas."""

from __future__ import annotations

from dataclasses import dataclass

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import PERMISOS, ROLES
from src.models import Usuario


class ErrorAutenticacion(Exception):
    """Usuario o contraseña inválidos, o datos de usuario incorrectos."""


@dataclass(frozen=True)
class UsuarioSesion:
    """Datos del usuario conectado que se guardan en ``st.session_state``."""

    id: int
    nombre: str
    usuario: str
    rol: str


def hash_contrasena(contrasena: str) -> str:
    """Genera el hash bcrypt de una contraseña."""
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    """Comprueba una contraseña contra su hash bcrypt."""
    try:
        return bcrypt.checkpw(contrasena.encode("utf-8"), hash_guardado.encode("utf-8"))
    except ValueError:
        return False


def autenticar(sesion: Session, usuario: str, contrasena: str) -> UsuarioSesion:
    """Valida las credenciales y devuelve el usuario conectado."""
    registro = sesion.scalar(select(Usuario).where(Usuario.usuario == usuario.strip().lower()))
    if registro is None or not registro.activo or not verificar_contrasena(contrasena, registro.hash_contrasena):
        raise ErrorAutenticacion("Usuario o contraseña incorrectos.")
    return UsuarioSesion(registro.id, registro.nombre, registro.usuario, registro.rol)


def crear_usuario(sesion: Session, nombre: str, usuario: str, contrasena: str, rol: str) -> Usuario:
    """Crea un usuario nuevo validando rol, nombre único y largo de contraseña."""
    usuario = usuario.strip().lower()
    if not nombre.strip() or not usuario:
        raise ErrorAutenticacion("El nombre y el usuario son obligatorios.")
    if rol not in ROLES:
        raise ErrorAutenticacion(f"Rol no válido: {rol}.")
    if len(contrasena) < 6:
        raise ErrorAutenticacion("La contraseña debe tener al menos 6 caracteres.")
    if sesion.scalar(select(Usuario).where(Usuario.usuario == usuario)) is not None:
        raise ErrorAutenticacion(f"El usuario '{usuario}' ya existe.")
    nuevo = Usuario(nombre=nombre.strip(), usuario=usuario, hash_contrasena=hash_contrasena(contrasena), rol=rol)
    sesion.add(nuevo)
    sesion.flush()
    return nuevo


def puede_ver(rol: str, pagina: str) -> bool:
    """Indica si un rol tiene acceso a una página (clave de ``PERMISOS``)."""
    return rol in PERMISOS.get(pagina, ())


# --- Integración con Streamlit -----------------------------------------------

def usuario_actual() -> UsuarioSesion | None:
    """Usuario guardado en la sesión de Streamlit, o ``None``."""
    import streamlit as st

    return st.session_state.get("usuario")


def proteger_pagina(pagina: str) -> UsuarioSesion:
    """Detiene la página si no hay sesión o si el rol no tiene permiso."""
    import streamlit as st

    usuario = usuario_actual()
    if usuario is None:
        st.warning("Inicie sesión desde la página principal para continuar.")
        st.stop()
    if not puede_ver(usuario.rol, pagina):
        st.error("Su rol no tiene acceso a esta página.")
        st.stop()
    return usuario
