"""Conteo de zapatos o cajas en una foto con Ultralytics YOLO-World.

Si el modelo no se puede descargar o falla, las funciones lanzan
``ErrorVision`` y la interfaz deja el conteo manual.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

from src.config import CLASES_YOLO, COLOR_ACENTO, FOTOS_DIR, MODELOS_DIR, MODELO_YOLO, UMBRAL_CONFIANZA

log = logging.getLogger(__name__)

MODO_PARES = "pares"
MODO_CAJAS = "cajas"
#: Modo de conteo → clase de YOLO-World que se cuenta.
CLASE_POR_MODO: dict[str, str] = {MODO_PARES: "shoe", MODO_CAJAS: "shoe box"}


class ErrorVision(Exception):
    """El modelo de visión no está disponible o falló al procesar la foto."""


@dataclass
class Deteccion:
    """Un objeto detectado en la foto."""

    clase: str
    confianza: float
    caja: tuple[float, float, float, float]  # x1, y1, x2, y2


@dataclass
class ResultadoConteo:
    """Resultado del conteo por imagen."""

    cantidad: int
    confianza_promedio: float
    imagen_anotada: Image.Image
    detecciones: list[Deteccion] = field(default_factory=list)
    objetos_detectados: int = 0


@st.cache_resource(show_spinner="Cargando el modelo de visión (solo la primera vez)…")
def cargar_modelo() -> Any:
    """Carga YOLO-World una sola vez y fija las clases personalizadas."""
    from ultralytics import YOLOWorld
    from ultralytics.nn import text_model

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    # El modelo de texto CLIP se guarda junto a los pesos de YOLO, no en ./weights.
    text_model.WEIGHTS_DIR = MODELOS_DIR
    modelo = YOLOWorld(str(MODELOS_DIR / MODELO_YOLO))
    modelo.set_classes(CLASES_YOLO)
    return modelo


def modelo_disponible() -> tuple[bool, str]:
    """Intenta cargar el modelo. Devuelve ``(disponible, mensaje)``."""
    try:
        cargar_modelo()
        return True, "Modelo YOLO-World listo."
    except Exception as exc:  # noqa: BLE001 — cualquier fallo deja el conteo manual
        log.exception("No se pudo cargar YOLO-World")
        return False, f"El conteo automático no está disponible ({type(exc).__name__}). Use el conteo manual."


def pares_desde_zapatos(zapatos: int) -> int:
    """Convierte zapatos sueltos a pares (÷ 2, redondeando la mitad hacia arriba)."""
    return (zapatos + 1) // 2


def _fuente(tamano: int) -> ImageFont.ImageFont:
    for nombre in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def anotar_imagen(imagen: Image.Image, detecciones: list[Deteccion]) -> Image.Image:
    """Dibuja los recuadros numerados sobre una copia de la imagen."""
    anotada = imagen.convert("RGB").copy()
    dibujo = ImageDraw.Draw(anotada)
    grosor = max(2, round(min(anotada.size) / 250))
    fuente = _fuente(max(14, round(min(anotada.size) / 28)))
    for i, det in enumerate(detecciones, start=1):
        x1, y1, x2, y2 = det.caja
        dibujo.rectangle((x1, y1, x2, y2), outline=COLOR_ACENTO, width=grosor)
        etiqueta = f"{i}"
        caja_txt = dibujo.textbbox((x1, y1), etiqueta, font=fuente)
        ancho, alto = caja_txt[2] - caja_txt[0] + 10, caja_txt[3] - caja_txt[1] + 8
        y_txt = max(0, y1 - alto)
        dibujo.rectangle((x1, y_txt, x1 + ancho, y_txt + alto), fill=COLOR_ACENTO)
        dibujo.text((x1 + 5, y_txt + 2), etiqueta, fill="white", font=fuente)
    return anotada


def contar_objetos(
    imagen: Image.Image, umbral: float = UMBRAL_CONFIANZA, modo: str = MODO_PARES,
) -> ResultadoConteo:
    """Cuenta pares de zapatos (zapatos ÷ 2) o cajas (1 caja = 1 par) en la foto."""
    if modo not in CLASE_POR_MODO:
        raise ValueError(f"Modo de conteo no válido: {modo}")
    imagen = ImageOps.exif_transpose(imagen).convert("RGB")
    try:
        modelo = cargar_modelo()
        resultados = modelo.predict(imagen, conf=umbral, verbose=False)
    except Exception as exc:  # noqa: BLE001
        log.exception("Fallo de YOLO-World al predecir")
        raise ErrorVision("No se pudo analizar la foto con el modelo de visión.") from exc

    clase_objetivo = CLASE_POR_MODO[modo]
    detecciones: list[Deteccion] = []
    for res in resultados:
        nombres = res.names
        for caja in res.boxes:
            clase = nombres[int(caja.cls.item())]
            if clase != clase_objetivo:
                continue
            x1, y1, x2, y2 = (float(v) for v in caja.xyxy[0].tolist())
            detecciones.append(Deteccion(clase, float(caja.conf.item()), (x1, y1, x2, y2)))
    detecciones.sort(key=lambda d: (d.caja[1], d.caja[0]))

    n = len(detecciones)
    cantidad = pares_desde_zapatos(n) if modo == MODO_PARES else n
    confianza = sum(d.confianza for d in detecciones) / n if n else 0.0
    return ResultadoConteo(cantidad, confianza, anotar_imagen(imagen, detecciones), detecciones, n)


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "-", texto).strip("-").lower()


def guardar_foto(imagen: Image.Image, fecha: date, tienda: str, producto: str) -> Path:
    """Guarda la foto original como evidencia en ``data/fotos/AAAA-MM-DD_tienda_producto.jpg``."""
    FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    ruta = FOTOS_DIR / f"{fecha:%Y-%m-%d}_{_slug(tienda)}_{_slug(producto)}.jpg"
    ImageOps.exif_transpose(imagen).convert("RGB").save(ruta, "JPEG", quality=90)
    return ruta
