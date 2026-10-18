# Manaco Data

Plataforma web **local** para la empresa boliviana de calzado **Manaco**. Resuelve dos problemas del caso de estudio:

1. **Inventario sin control diario.** Registra la apertura, las ventas y el cierre de stock de pares de zapatos en cada tienda, cuenta el stock con una **foto** (IA YOLO-World) y **alerta** cuando lo contado no coincide con lo esperado.
2. **Datos sin integrar.** Un **tablero de mercado** analiza la base de comercio exterior de calzado (Excel) junto con las ventas internas registradas en el sistema.

Tecnología: Python 3.11 · Streamlit · SQLite + SQLAlchemy 2 · pandas · Plotly · Ultralytics YOLO-World · bcrypt · pytest.

---

## Instalación con Anaconda

Abra **Anaconda Prompt** (o PowerShell con `conda init powershell` ya ejecutado) en la carpeta del proyecto:

```bash
conda env create -f environment.yml
conda activate manaco
python scripts/init_db.py      # crea las tablas, carga el Excel y el usuario admin
python scripts/seed_demo.py    # (opcional) 3 tiendas, 12 productos y 30 días de operación
streamlit run app.py
```

Se abre en el navegador en `http://localhost:8501`. Para usarlo desde el celular (tomar la foto), conéctelo a la misma red Wi-Fi y abra la dirección *Network URL* que muestra Streamlit.

> La primera vez que se usa el conteo por foto se descargan el modelo `yolov8s-world.pt` (~25 MB) y el modelo de texto CLIP (~340 MB) en `data/modelos/` (en esta computadora ya están descargados). Se necesita internet solo esa vez. Si no hay conexión, el sistema sigue funcionando con el conteo manual.

### Usuarios de prueba

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `manaco2026` | administrador (ve todo) |
| `encargado` | `manaco2026` | encargado (apertura, ventas, cierre) — lo crea `seed_demo.py` |
| `gerencia` | `manaco2026` | gerencia (inicio, historial, tablero) — lo crea `seed_demo.py` |

⚠️ **Cambie estas contraseñas** en la página *Usuarios* antes de usar el sistema con datos reales.

---

## Páginas

| Página | Rol | Qué hace |
| --- | --- | --- |
| **Inicio** | admin, gerencia | Cuatro KPI del día (pares en apertura, vendidos, cierres hechos/pendientes, alertas activas), la lista de alertas pendientes y el gráfico de diferencias de los últimos 30 días. |
| **Apertura** | admin, encargado | Registra el saldo inicial por fecha, tienda y producto. Propone el conteo del cierre de ayer. Permite abrir todos los productos de una tienda a la vez. |
| **Ventas** | admin, encargado | Formulario rápido de venta, tabla de ventas del día y stock disponible en tiempo real (saldo inicial − vendido). |
| **Cierre y conteo** | admin, encargado | Muestra inicial, vendido y esperado; recibe la foto (cámara o archivo), cuenta con IA, permite corregir a mano y guarda el cierre con su alerta de color. |
| **Historial** | admin, gerencia | Planilla de cierres con filtros y colores por estado; permite ver la foto de evidencia y descargar un **Excel** con formato y hoja de resumen. |
| **Tablero de mercado** | admin, gerencia | KPI y 3 gráficos del comercio exterior limpio (230 registros válidos), filtros, selector de métrica, limitaciones de los datos y la pestaña *Datos internos*. |
| **Catálogo** | admin | Alta, edición y baja (desactivación) de productos y tiendas. |
| **Usuarios** | admin | Alta de usuarios, roles, desactivación y cambio de contraseña. |

### Reglas de inventario

- **Saldo esperado** = saldo inicial − total vendido del día.
- **Diferencia** = conteo final − saldo esperado → `Correcto` (0 o dentro de la tolerancia), `Faltante` (negativa) o `Sobrante` (positiva).
- No hay ventas sin apertura, ni ventas que superen el stock, ni cierres sin apertura.
- Un cierre guardado no se repite; solo el administrador lo anula, indicando un motivo (queda en `anulaciones_cierre`).
- La tolerancia se ajusta en `src/config.py` (`TOLERANCIA_DIFERENCIA`, por defecto 0).

Ejemplo: apertura 50, ventas 12 → esperado 38; conteo 36 → diferencia −2 → **"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"**.

### Limpieza del Excel

`src/services/etl.py` aplica y registra en `bitacora_limpieza`:
1. Validación de tipos y faltantes (0 faltantes).
2. Separación de registros con socio "Mundo" (0 en la base actual).
3. Claves repetidas (Flujo, Año, Código SA6, Socio): se conserva la primera → **240 → 230 válidas, 10 descartadas**.
4. Consistencia `Valor_USD ≈ Valor_miles_USD × 1000` y `Valor_USD_por_par ≈ Valor_USD / Cantidad_pares`.

Totales válidos: importación **17.055,8 M USD**, exportación **10.605,5 M USD**.

---

## Guion de demo (2 minutos)

Antes: `python scripts/seed_demo.py` y `streamlit run app.py`. Ingrese como `admin`.

1. **Inicio (15 s).** Muestre los KPI y las alertas pendientes de la última semana: "el sistema detecta faltantes cada día".
2. **Apertura (20 s).** Tienda Prado → pestaña *Toda la tienda*: los saldos ya vienen propuestos desde el cierre de ayer → *Abrir 12 productos*.
3. **Ventas (20 s).** Venda 2 pares de `MAN-DEP-001`; el stock disponible baja al instante. Intente vender más de lo disponible: aparece el error claro.
4. **Foto (30 s).** *Cierre y conteo* → `MAN-DEP-001` → *Cámara* (o suba una foto de zapatos) → *Contar con IA*: se ven los recuadros numerados, el conteo y la confianza.
5. **Alerta (15 s).** Corrija el conteo final a 2 menos que el esperado → *Calcular y guardar cierre* → aparece la alerta roja "Faltan 2 pares…".
6. **Historial (10 s).** Filtre por estado *Faltante*, seleccione la fila para ver la foto y descargue el Excel.
7. **Tablero (10 s).** 230 registros válidos, los 3 gráficos y el cambio de métrica Valor USD / Cantidad de pares, que cambia la conclusión.

---

## Estructura

```
app.py                 Inicio, login y navegación por rol
pages/                 Apertura, Ventas, Cierre y conteo, Historial, Tablero, Catálogo, Usuarios
src/config.py          Rutas, constantes, permisos y tolerancia
src/db.py, models.py   SQLite + SQLAlchemy
src/auth.py            Login, roles y bcrypt
src/services/          inventario (reglas), vision (YOLO-World), etl (Excel), reportes (Excel de salida)
src/ui/                estilos (CSS y tarjetas KPI), graficos (Plotly), comunes (selectores)
scripts/               init_db.py, seed_demo.py
tests/                 pytest: reglas de inventario y ETL
data/                  raw/ (Excel), fotos/ (evidencia), modelos/ (pesos YOLO), manaco.db
```

Pruebas: `python -m pytest`

---

## Limitaciones

- La base de comercio exterior es de **España**, no de Bolivia; sirve como referencia internacional.
- El **valor por par** es un valor aduanero, no el precio al consumidor.
- La **cobertura por año es desigual** (28 a 82 registros por año).
- El conteo por foto con YOLO-World es *zero-shot*: funciona mejor con zapatos o cajas bien separados, buena luz y vista frontal. Con pilas apretadas conviene contar cajas o corregir a mano.
- Es un sistema local de un solo servidor con SQLite; no está pensado para muchos usuarios simultáneos en red.

## Próximos pasos

- Ajustar (*fine-tuning*) un detector con fotos reales de las tiendas Manaco.
- Integrar con el punto de venta para registrar ventas automáticamente.
- Migrar a PostgreSQL y desplegar en un servidor de la empresa con HTTPS.
- Incorporar datos de comercio exterior de Bolivia (INE / Aduana Nacional).
- Reportes automáticos por correo y control de traspasos entre tiendas.

## Publicar en Streamlit Community Cloud

1. Entre a [share.streamlit.io](https://share.streamlit.io) con su cuenta de GitHub → **Create app**.
2. Repositorio `edisonayala000-netizen/manaco-data`, rama `main`, archivo `app.py`; en *Advanced settings* elija **Python 3.11** → **Deploy**.
3. La primera vez que se abre, si la base no tiene usuarios, `app.py` ejecuta solo `init_db.py` y `seed_demo.py` (Excel, usuario `admin` y datos de demo).

`packages.txt` instala las librerías del sistema que necesita OpenCV, y `requirements.txt` usa PyTorch para CPU. En el plan gratuito los datos se reinician cuando la app se reinicia, y el conteo por foto puede no caber en la memoria disponible; en ese caso el sistema avisa y deja el conteo manual.

## Diseño y capturas

La identidad visual (paleta, tipografías Plus Jakarta Sans e Inter, íconos Material, tarjetas, banners y alertas) está centralizada en `src/ui/estilos.py`; los gráficos usan la plantilla Plotly `manaco` de `src/ui/graficos.py`. Para regenerar las capturas de `docs/capturas/`:

```bash
pip install playwright
streamlit run app.py --server.headless true --server.port 8502   # en otra terminal
python scripts/capturar_pantallas.py
```
