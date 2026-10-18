"""Pruebas del conteo por foto que no requieren descargar el modelo."""

from __future__ import annotations

from datetime import date

import pytest
from PIL import Image

from src.services import vision


@pytest.mark.parametrize(("zapatos", "pares"), [(0, 0), (1, 1), (2, 1), (5, 3), (8, 4)])
def test_pares_desde_zapatos(zapatos, pares):
    assert vision.pares_desde_zapatos(zapatos) == pares


def test_anotar_imagen_no_modifica_original():
    original = Image.new("RGB", (200, 120), "white")
    det = [vision.Deteccion("shoe", 0.9, (10, 30, 80, 100))]
    anotada = vision.anotar_imagen(original, det)
    assert anotada.size == original.size
    assert anotada.getpixel((10, 60)) != (255, 255, 255)
    assert original.getpixel((10, 60)) == (255, 255, 255)


def test_si_el_modelo_falla_se_informa_sin_caer(monkeypatch):
    def _falla():
        raise OSError("sin conexión")

    monkeypatch.setattr(vision, "cargar_modelo", _falla)
    disponible, mensaje = vision.modelo_disponible()
    assert not disponible and "manual" in mensaje
    with pytest.raises(vision.ErrorVision):
        vision.contar_objetos(Image.new("RGB", (64, 64)))


def test_guardar_foto_nombre_evidencia(tmp_path, monkeypatch):
    monkeypatch.setattr(vision, "FOTOS_DIR", tmp_path)
    ruta = vision.guardar_foto(Image.new("RGB", (32, 32)), date(2026, 10, 16), "Tienda Heroínas", "MAN-DEP-001")
    assert ruta.name == "2026-10-16_tienda-heroinas_man-dep-001.jpg"
    assert ruta.exists()
