"""Cierre del día: asistente en 3 pasos (seleccionar, contar con foto o a mano, resultado)."""

from __future__ import annotations

import streamlit as st
from PIL import Image, UnidentifiedImageError

from src.auth import proteger_pagina
from src.config import ROL_ADMIN, UMBRAL_CONFIANZA
from src.db import obtener_sesion
from src.services import inventario as inv
from src.services import vision
from src.services.inventario import ErrorNegocio
from src.ui.comunes import (
    avisar_y_recargar, exigir_catalogo, mostrar_aviso_pendiente, selector_fecha, selector_producto,
    selector_tienda,
)
from src.ui.estilos import (
    ICONOS, aviso, conteo_grande, encabezado, estado_vacio, fecha as ffecha, num, pasos, tarjeta, tarjeta_kpi,
    tarjeta_resultado,
)

usuario = proteger_pagina("cierre")
encabezado("Cierre y conteo", "Cuente el stock con una foto o a mano y compare con lo esperado.", ICONOS["cierre"])
mostrar_aviso_pendiente()
tiendas, productos = exigir_catalogo()
indicador = st.empty()

# --- Paso 1: seleccionar -------------------------------------------------------
with tarjeta("seleccion", "1. Seleccionar", "Elija la fecha, la tienda y el producto que va a cerrar.", "checklist"):
    c1, c2, c3 = st.columns(3)
    dia = selector_fecha("ci_fecha", c1)
    tienda_id, tienda_nombre = selector_tienda(tiendas, "ci_tienda", c2)
    with obtener_sesion() as s:
        abiertos_df = inv.tabla_aperturas(s, dia, tienda_id)
    if abiertos_df.empty:
        with indicador:
            pasos(1)
        estado_vacio(f"No hay aperturas en {tienda_nombre} el {ffecha(dia)}: no se puede cerrar sin apertura.",
                     "inventory_2", ("Ir a Apertura", "pages/1_Apertura.py", "inventory_2"), clave="cierre")
        st.stop()
    abiertos = productos[productos["codigo"].isin(abiertos_df["Código"])]
    producto = selector_producto(abiertos, "ci_producto", c3)
    producto_id = int(producto["id"])

    with obtener_sesion() as s:
        resumen = inv.resumen_dia(s, dia, tienda_id, producto_id)
        cierre = inv.obtener_cierre(s, dia, tienda_id, producto_id)
        mensaje_cierre = inv.mensaje_alerta_cierre(cierre) if cierre else None

    k1, k2, k3 = st.columns(3)
    with k1:
        tarjeta_kpi("Saldo inicial", num(resumen.saldo_inicial), icono="inventory_2", color="azul", mini=True)
    with k2:
        tarjeta_kpi("Vendido hoy", num(resumen.total_vendido), icono="shopping_bag", color="verde", mini=True)
    with k3:
        tarjeta_kpi("Saldo esperado", num(resumen.saldo_esperado), "inicial − vendido", icono="calculate",
                    color="morado", mini=True)

with indicador:
    pasos(3 if cierre is not None else 2)
st.write("")

# --- Paso 3 (cierre ya guardado): resultado --------------------------------------
if cierre is not None:
    with tarjeta("resultado", "3. Resultado", "Este cierre ya fue guardado y no se puede repetir.", "fact_check"):
        tarjeta_resultado(cierre.estado, mensaje_cierre, cierre.saldo_esperado, cierre.conteo_final, cierre.diferencia)
        d1, d2 = st.columns([1, 1.4], gap="medium")
        with d1:
            tarjeta_kpi("Conteo IA", "—" if cierre.conteo_ia is None else str(cierre.conteo_ia),
                        None if cierre.confianza_ia is None else f"confianza {num(cierre.confianza_ia * 100, 0)} %",
                        icono="smart_toy", color="azul", mini=True)
            st.write("")
            tarjeta_kpi("Conteo final", str(cierre.conteo_final), "manual o confirmado", icono="edit_note",
                        color="morado", mini=True)
            if cierre.observacion:
                st.caption(f"Observación: {cierre.observacion}")
        with d2:
            if cierre.foto_ruta:
                try:
                    st.image(cierre.foto_ruta, caption="Foto de evidencia", width="stretch")
                except Exception:  # noqa: BLE001
                    estado_vacio("La foto de evidencia ya no está disponible en el disco.", "hide_image")
            else:
                estado_vacio("Cierre registrado sin foto (conteo manual).", "no_photography")
        if usuario.rol == ROL_ADMIN:
            with st.expander("Anular cierre (solo administrador)", icon=":material/undo:"), st.form("form_anular"):
                motivo = st.text_area("Motivo de la anulación", key="ci_motivo")
                if st.form_submit_button("Anular cierre", icon=":material/delete_history:"):
                    try:
                        with obtener_sesion() as s:
                            inv.anular_cierre(s, cierre.id, usuario.id, motivo)
                        avisar_y_recargar("Cierre anulado. Ya puede registrarlo de nuevo.", "warning")
                    except ErrorNegocio as exc:
                        aviso(str(exc), "error")
    st.stop()

# --- Paso 2: contar --------------------------------------------------------------
clave = f"conteo_{dia}_{tienda_id}_{producto_id}"
with tarjeta("conteo", "2. Contar", "Tome o suba una foto del estante; la IA cuenta y usted confirma.", "photo_camera"):
    a, b, c = st.columns([1, 1, 1.2])
    origen = a.segmented_control("Origen de la foto", ["Subir archivo", "Cámara"], default="Subir archivo",
                                 key="ci_origen") or "Subir archivo"
    modo = b.segmented_control("¿Qué se cuenta?", ["Pares", "Cajas"], default="Pares", key="ci_modo",
                               help="Pares: zapatos sueltos ÷ 2 · Cajas: 1 caja = 1 par") or "Pares"
    umbral = c.slider("Umbral de confianza", 0.05, 0.90, UMBRAL_CONFIANZA, 0.05, key="ci_umbral",
                      help="Más bajo detecta más objetos (y más errores); más alto es más estricto.")
    modo_vision = vision.MODO_PARES if modo == "Pares" else vision.MODO_CAJAS

    archivo = (st.camera_input("Tome la foto del estante o las cajas", key="ci_camara") if origen == "Cámara"
               else st.file_uploader("Foto (JPG o PNG)", type=["jpg", "jpeg", "png", "webp"], key="ci_archivo"))
    imagen: Image.Image | None = None
    if archivo is not None:
        try:
            imagen = Image.open(archivo)
            imagen.load()
        except (UnidentifiedImageError, OSError):
            aviso("No se pudo leer la imagen. Pruebe con otra foto en formato JPG o PNG.", "error")

    if imagen is not None and st.button("Contar con IA", type="primary", icon=":material/auto_awesome:"):
        with st.spinner("Analizando la foto…"):
            disponible, mensaje = vision.modelo_disponible()
            if not disponible:
                st.session_state.pop(clave, None)
                aviso(mensaje, "warning")
            else:
                try:
                    st.session_state[clave] = vision.contar_objetos(imagen, umbral, modo_vision)
                except vision.ErrorVision as exc:
                    st.session_state.pop(clave, None)
                    aviso(f"{exc} Ingrese el conteo manualmente.", "warning")

    resultado: vision.ResultadoConteo | None = st.session_state.get(clave)
    if imagen is not None:
        f1, f2, f3 = st.columns([1, 1, 0.8], gap="medium")
        f1.image(imagen, caption="Foto original", width="stretch")
        if resultado is not None:
            f2.image(resultado.imagen_anotada, caption="Detecciones de la IA", width="stretch")
            with f3:
                conteo_grande(resultado.cantidad, "pares" if modo_vision == vision.MODO_PARES else "cajas",
                              resultado.confianza_promedio, resultado.objetos_detectados)
                if resultado.objetos_detectados == 0:
                    aviso("No se detectaron objetos. Baje el umbral o cuente manualmente.", "warning")
        else:
            with f2:
                estado_vacio("Pulse «Contar con IA» para ver las detecciones.", "auto_awesome")

    st.divider()
    conteo_ia = resultado.cantidad if resultado is not None and imagen is not None else None
    g1, g2 = st.columns([1, 2])
    conteo_final = g1.number_input(
        "Conteo final (pares)", min_value=0, step=1, value=conteo_ia, key=f"ci_final_{clave}_{conteo_ia}",
        placeholder="Ingrese el conteo", help="Puede corregir el valor de la IA; se guardan ambos.",
    )
    observacion = g2.text_input("Observación (opcional)", key="ci_obs")

    if st.button("Calcular y guardar cierre", type="primary", icon=":material/task_alt:"):
        if conteo_final is None:
            aviso("Ingrese el conteo final antes de guardar.", "error")
        else:
            try:
                ruta = None
                if imagen is not None:
                    ruta = str(vision.guardar_foto(imagen, dia, tienda_nombre, producto["codigo"]))
                with obtener_sesion() as s:
                    nuevo = inv.registrar_cierre(
                        s, dia, tienda_id, producto_id, int(conteo_final), usuario.id,
                        conteo_ia=conteo_ia,
                        confianza_ia=resultado.confianza_promedio if conteo_ia is not None else None,
                        foto_ruta=ruta, observacion=observacion,
                    )
                    estado = nuevo.estado
                st.session_state.pop(clave, None)
                avisar_y_recargar(f"Cierre guardado con estado {estado}.",
                                  {"Correcto": "success", "Sobrante": "warning"}.get(estado, "error"))
            except ErrorNegocio as exc:
                aviso(str(exc), "error")
            except OSError:
                aviso("No se pudo guardar la foto de evidencia. Revise el espacio en disco e intente de nuevo.", "error")
