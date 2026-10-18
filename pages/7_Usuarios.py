"""Administración de usuarios y roles (solo administrador)."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.auth import ErrorAutenticacion, crear_usuario, hash_contrasena, proteger_pagina
from src.config import ROLES
from src.db import obtener_sesion
from src.models import Usuario
from src.ui.comunes import avisar_y_recargar, mostrar_aviso_pendiente
from src.ui.estilos import ICONOS, aviso, encabezado, ficha_usuario, grilla, seccion, tarjeta

actual = proteger_pagina("usuarios")
encabezado("Usuarios", "Cree cuentas, asigne roles y desactive accesos.", ICONOS["usuarios"])
mostrar_aviso_pendiente()

with obtener_sesion() as s:
    usuarios = pd.DataFrame([{
        "id": u.id, "Nombre": u.nombre, "Usuario": u.usuario, "Rol": u.rol, "Activo": u.activo,
        "Creado": u.creado_en.strftime("%d/%m/%Y") if u.creado_en else "",
    } for u in s.scalars(select(Usuario).order_by(Usuario.usuario)).all()],
        columns=["id", "Nombre", "Usuario", "Rol", "Activo", "Creado"])

seccion(f"{len(usuarios)} usuarios",
        "Administrador: todo · Encargado: apertura, ventas y cierre · Gerencia: inicio, historial y tablero")
grilla([ficha_usuario(r["Nombre"], r["Usuario"], r["Rol"], bool(r["Activo"])) for _, r in usuarios.iterrows()])

with tarjeta("tabla", "Editar usuarios", "Cambie el nombre, el rol o desactive el acceso.", "manage_accounts"):
    editado = st.data_editor(
        usuarios, hide_index=True, width="stretch", key="usr_editor",
        disabled=["id", "Usuario", "Creado"],
        column_config={"id": None, "Rol": st.column_config.SelectboxColumn(options=list(ROLES), required=True)},
    )
    if st.button("Guardar cambios", type="primary", icon=":material/save:"):
        propio = editado[editado["id"] == actual.id]
        if not propio.empty and (propio["Rol"].iloc[0] != "administrador" or not propio["Activo"].iloc[0]):
            aviso("No puede quitarse a sí mismo el rol de administrador ni desactivar su propia cuenta.", "error")
        else:
            with obtener_sesion() as s:
                for _, fila in editado.iterrows():
                    u = s.get(Usuario, int(fila["id"]))
                    u.nombre, u.rol, u.activo = str(fila["Nombre"]).strip(), fila["Rol"], bool(fila["Activo"])
            avisar_y_recargar("Usuarios actualizados.")

st.write("")
c1, c2 = st.columns(2, gap="medium")
with c1, tarjeta("nuevo", "Nuevo usuario", icono="person_add"), st.form("nuevo_usuario", clear_on_submit=True,
                                                                         border=False):
    nombre = st.text_input("Nombre completo")
    usuario = st.text_input("Usuario (para ingresar)", icon=":material/person:")
    rol = st.selectbox("Rol", list(ROLES), index=1)
    contrasena = st.text_input("Contraseña", type="password", help="Mínimo 6 caracteres.", icon=":material/lock:")
    if st.form_submit_button("Crear usuario", type="primary", icon=":material/person_add:"):
        try:
            with obtener_sesion() as s:
                crear_usuario(s, nombre, usuario, contrasena, rol)
            avisar_y_recargar(f"Usuario '{usuario.strip().lower()}' creado con rol {rol}.")
        except ErrorAutenticacion as exc:
            aviso(str(exc), "error")

with c2, tarjeta("clave", "Cambiar contraseña", icono="key"), st.form("cambiar_clave", clear_on_submit=True,
                                                                       border=False):
    elegido = st.selectbox("Usuario", usuarios["Usuario"].tolist())
    nueva = st.text_input("Nueva contraseña", type="password", icon=":material/lock:")
    repetir = st.text_input("Repita la contraseña", type="password", icon=":material/lock:")
    if st.form_submit_button("Actualizar contraseña", type="primary", icon=":material/key:"):
        if len(nueva) < 6:
            aviso("La contraseña debe tener al menos 6 caracteres.", "error")
        elif nueva != repetir:
            aviso("Las contraseñas no coinciden.", "error")
        else:
            with obtener_sesion() as s:
                u = s.scalar(select(Usuario).where(Usuario.usuario == elegido))
                u.hash_contrasena = hash_contrasena(nueva)
            avisar_y_recargar(f"Contraseña de '{elegido}' actualizada.")
