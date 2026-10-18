"""Capturas de pantalla de cada página con Playwright (para revisar el diseño).

Requiere la app corriendo, por ejemplo:
    streamlit run app.py --server.headless true --server.port 8502
Uso:
    python scripts/capturar_pantallas.py [url]

Usa el Chrome instalado en el equipo (``channel="chrome"``); si no existe, el Chromium de Playwright.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = Path(__file__).resolve().parent.parent
SALIDA = BASE / "docs" / "capturas"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"
USUARIO, CONTRASENA = "admin", "manaco2026"  # usuario de prueba creado por scripts/init_db.py


def esperar(page: Page, extra_ms: int = 900) -> None:
    """Espera a que Streamlit termine de ejecutar la página y se dibujen los gráficos."""
    page.wait_for_function(
        "() => { const a = document.querySelector('.stApp');"
        " return a && a.getAttribute('data-test-script-state') !== 'running'; }", timeout=90_000)
    page.wait_for_timeout(extra_ms)


def capturar(page: Page, nombre: str, ancho: int) -> None:
    """Captura la página completa ajustando el alto de la ventana al contenido."""
    alto = page.evaluate(
        "() => { const m = document.querySelector('[data-testid=\"stMain\"]') || document.body;"
        " return Math.max(m.scrollHeight, window.innerHeight); }")
    page.set_viewport_size({"width": ancho, "height": min(int(alto) + 40, 7000)})
    page.wait_for_timeout(600)
    page.screenshot(path=str(SALIDA / f"{nombre}.png"), full_page=True)
    page.set_viewport_size({"width": ancho, "height": 860})
    print(f"✔ {nombre}.png")


def ingresar(page: Page) -> None:
    page.goto(URL)
    page.wait_for_selector("text=Bienvenido", timeout=60_000)
    esperar(page)
    page.get_by_label("Usuario").fill(USUARIO)
    page.get_by_label("Contraseña").fill(CONTRASENA)
    page.get_by_role("button", name="Ingresar").click()
    page.wait_for_selector('[data-testid="stSidebarNav"]', state="attached", timeout=60_000)
    esperar(page)


def ir(page: Page, titulo: str, movil: bool = False) -> None:
    """Navega con el menú lateral (navegar por URL abriría otra sesión)."""
    enlace = page.locator('[data-testid="stSidebarNavLink"]', has_text=titulo).first
    if movil and not enlace.is_visible():
        page.locator('[data-testid="stExpandSidebarButton"]').first.click()
        page.wait_for_timeout(1200)
    enlace.evaluate("e => e.click()")
    esperar(page, 1400)


def pestana(page: Page, texto: str) -> None:
    page.get_by_role("tab", name=texto).click()
    esperar(page, 1200)


def elegir(page: Page, etiqueta: str, texto: str) -> None:
    """Elige una opción de un selectbox escribiendo parte del texto."""
    page.get_by_label(etiqueta).first.click()
    page.keyboard.type(texto)
    page.keyboard.press("Enter")
    esperar(page, 1200)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(channel="chrome")
        except Exception:  # noqa: BLE001
            navegador = p.chromium.launch()

        # --- Escritorio (1366 px) ---
        page = navegador.new_page(viewport={"width": 1366, "height": 860}, locale="es-BO")
        page.goto(URL)
        page.wait_for_selector("text=Bienvenido", timeout=60_000)
        esperar(page, 1500)
        capturar(page, "01_login", 1366)
        ingresar(page)
        capturar(page, "02_inicio", 1366)
        for nombre, titulo in (("03_apertura", "Apertura"), ("04_ventas", "Ventas")):
            ir(page, titulo)
            elegir(page, "Tienda", "Prado")
            capturar(page, nombre, 1366)
        ir(page, "Cierre y conteo")
        elegir(page, "Tienda", "Prado")
        elegir(page, "Producto", "MAN-CUE-001")
        capturar(page, "05_cierre_resultado", 1366)
        elegir(page, "Producto", "MAN-CYC-001")
        page.wait_for_selector('[data-testid="stFileUploaderDropzone"]', timeout=60_000)
        esperar(page, 1500)
        capturar(page, "06_cierre_contar", 1366)
        ir(page, "Historial")
        capturar(page, "07_historial", 1366)
        ir(page, "Tablero de mercado")
        capturar(page, "08_tablero_mercado", 1366)
        pestana(page, "Datos internos")
        capturar(page, "09_tablero_internos", 1366)
        pestana(page, "Limpieza de datos")
        capturar(page, "10_tablero_limpieza", 1366)
        ir(page, "Catálogo")
        capturar(page, "11_catalogo", 1366)
        ir(page, "Usuarios")
        capturar(page, "12_usuarios", 1366)
        page.close()

        # --- Celular (390 px) ---
        movil = navegador.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                   is_mobile=True, has_touch=True, locale="es-BO")
        movil.goto(URL)
        movil.wait_for_selector("text=Bienvenido", timeout=60_000)
        esperar(movil, 1500)
        capturar(movil, "13_movil_login", 390)
        ingresar(movil)
        capturar(movil, "14_movil_inicio", 390)
        ir(movil, "Cierre y conteo", movil=True)
        capturar(movil, "15_movil_cierre", 390)
        navegador.close()


if __name__ == "__main__":
    main()
