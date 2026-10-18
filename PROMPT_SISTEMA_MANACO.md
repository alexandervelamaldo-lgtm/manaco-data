# Prompt para construir "Manaco Data" — sistema web local

> Cómo usarlo: coloca este archivo y el Excel `Base_de_Datos_MANACO.xlsx` en una carpeta nueva y vacía. Abre la terminal (Anaconda Prompt) en esa carpeta, ejecuta `claude` y escribe:
> **"Lee PROMPT_SISTEMA_MANACO.md y construye el sistema completo siguiendo todas sus instrucciones."**

---

## 1. Rol y objetivo

Actúa como un ingeniero de software senior especializado en Python, ciencia de datos e interfaces web. Construye en esta carpeta un sistema web **local**, profesional y listo para presentar en una defensa universitaria: **"Manaco Data"**, una plataforma para la empresa boliviana de calzado Manaco.

El sistema resuelve dos problemas del caso de estudio:
1. **Inventario sin control diario.** Controla la apertura, las ventas y el cierre de stock de pares de zapatos, cuenta el stock con una foto y alerta cuando hay diferencias.
2. **Datos sin integrar.** Tiene un tablero que analiza la base de comercio exterior de calzado (el Excel) junto con los datos internos de inventario y ventas.

Todo el sistema (interfaz, mensajes, comentarios y documentación) va **en español**. El código debe ser limpio, modular, con type hints y docstrings, y tener calidad de producción.

Trabaja por etapas (sección 10). Al terminar cada etapa, ejecuta las pruebas y verifica que funciona antes de pasar a la siguiente.

---

## 2. Tecnología (obligatoria)

| Capa | Herramienta |
| --- | --- |
| Lenguaje | Python 3.11 (compatible con Anaconda) |
| Interfaz web | Streamlit (aplicación multipágina, carpeta `pages/`) |
| Base de datos | SQLite (archivo `data/manaco.db`) con SQLAlchemy 2.x |
| Datos | pandas, openpyxl |
| Gráficos | Plotly |
| Conteo por imagen | Ultralytics **YOLO-World** (`yolov8s-world.pt`) con clases personalizadas `["shoe", "shoe box"]`, más Pillow y OpenCV |
| Contraseñas | bcrypt |
| Pruebas | pytest |

Crea `requirements.txt` y `environment.yml` (nombre del entorno: `manaco`).

---

## 3. Estructura del proyecto

```
manaco_data/
├── app.py                      # Página de inicio (resumen del día)
├── pages/
│   ├── 1_Apertura.py
│   ├── 2_Ventas.py
│   ├── 3_Cierre_y_conteo.py
│   ├── 4_Historial.py
│   ├── 5_Tablero_de_mercado.py
│   ├── 6_Catalogo.py
│   └── 7_Usuarios.py           # solo administrador
├── src/
│   ├── config.py               # rutas, constantes, tolerancia de diferencia
│   ├── db.py                   # motor, sesión, creación de tablas
│   ├── models.py               # modelos SQLAlchemy
│   ├── auth.py                 # login, roles, hash de contraseñas
│   ├── services/
│   │   ├── inventario.py       # lógica de apertura, ventas y cierre (sin Streamlit)
│   │   ├── vision.py           # conteo por foto con YOLO-World
│   │   ├── etl.py              # carga y limpieza del Excel
│   │   └── reportes.py         # exportar a Excel
│   └── ui/
│       ├── estilos.py          # CSS y componentes visuales (tarjetas KPI, encabezados)
│       └── graficos.py         # funciones Plotly reutilizables
├── data/
│   ├── raw/Base_de_Datos_MANACO.xlsx
│   ├── fotos/                  # fotos de cierre guardadas como evidencia
│   └── manaco.db
├── scripts/
│   ├── init_db.py              # crea las tablas, carga el Excel y el usuario admin
│   └── seed_demo.py            # datos de demostración de 30 días
├── tests/
│   ├── test_inventario.py
│   └── test_etl.py
├── .streamlit/config.toml      # tema visual
├── requirements.txt
├── environment.yml
└── README.md
```

Al empezar, mueve el Excel que está en la carpeta raíz a `data/raw/Base_de_Datos_MANACO.xlsx`.

---

## 4. Modelo de datos (SQLite)

- **usuarios**: id, nombre, usuario (único), hash_contrasena, rol (`administrador` | `encargado` | `gerencia`), activo, creado_en
- **tiendas**: id, nombre, ciudad (La Paz, El Alto, Cochabamba, Santa Cruz, Sucre, Tarija, Oruro, Potosí), tipo (`tienda` | `almacén`)
- **productos**: id, codigo_modelo (único, p. ej. `MAN-DEP-001`), nombre, categoria (`Deportivo` | `Caucho y cuero` | `Cuero`), codigo_sa6 (640411 | 640399 | 640420), talla, color, precio_venta_bs, costo_bs, activo
- **aperturas**: id, fecha, tienda_id, producto_id, saldo_inicial, usuario_id, creado_en. **Única** por (fecha, tienda, producto).
- **ventas**: id, fecha, hora, tienda_id, producto_id, cantidad, precio_unitario_bs, usuario_id
- **cierres**: id, fecha, tienda_id, producto_id, saldo_inicial, total_vendido, saldo_esperado, conteo_ia (nullable), conteo_final, diferencia, estado (`Correcto` | `Faltante` | `Sobrante`), foto_ruta (nullable), confianza_ia (nullable), observacion, usuario_id, creado_en. **Único** por (fecha, tienda, producto).
- **comercio_exterior**: las 10 columnas del Excel ya limpias + columna `registro_valido`
- **bitacora_limpieza**: id, regla, filas_afectadas, detalle, fecha

---

## 5. Reglas de negocio (`src/services/inventario.py`)

Esta lógica va separada de la interfaz y tiene pruebas unitarias.

1. **Apertura.** Se registra el saldo inicial por fecha, tienda y producto. No se permiten duplicados ni valores negativos. Si existe el cierre del día anterior, se propone su `conteo_final` como saldo inicial.
2. **Ventas.** Solo se pueden registrar si existe la apertura del día. La cantidad debe ser mayor que 0, y la suma de ventas del día no puede superar el saldo inicial (se muestra un error claro).
3. **Saldo esperado** = saldo inicial − total vendido del día.
4. **Cierre.** Exige que exista la apertura. El conteo final viene de la IA o del ingreso manual; el manual siempre puede corregir al de la IA y se guardan ambos valores.
5. **Diferencia** = conteo final − saldo esperado. El estado es:
   - `Correcto` si la diferencia es 0 o está dentro de la tolerancia (configurable en `config.py`, por defecto 0).
   - `Faltante` si es negativa.
   - `Sobrante` si es positiva.
6. **Alerta.** Si el estado no es `Correcto`, se muestra una alerta roja o naranja bien visible, con el mensaje exacto: *"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"*. La alerta queda pendiente en la página de inicio.
7. **Cierre único.** Un cierre ya guardado no se puede volver a hacer; solo el administrador puede anularlo, con un motivo.
8. **Ejemplo de prueba obligatorio:** apertura 50, ventas 12 → esperado 38; conteo 36 → diferencia −2, estado `Faltante`.

---

## 6. Conteo por foto (`src/services/vision.py`)

- Función `contar_objetos(imagen: PIL.Image) -> ResultadoConteo(cantidad, confianza_promedio, imagen_anotada, detecciones)`.
- Usa `ultralytics.YOLOWorld("yolov8s-world.pt")` con `model.set_classes(["shoe", "shoe box"])`. Carga el modelo **una sola vez** con `@st.cache_resource`.
- Umbral de confianza ajustable con un deslizador (por defecto 0,25). Dibuja los recuadros numerados sobre la imagen.
- Un selector indica si se cuentan **pares** (zapatos sueltos: cantidad ÷ 2, redondeado) o **cajas** (cada caja es 1 par).
- La foto llega con `st.camera_input` (cámara de la laptop o del celular) o con `st.file_uploader`.
- Guarda la foto original en `data/fotos/AAAA-MM-DD_tienda_producto.jpg` como evidencia.
- **Si el modelo no se puede descargar o falla**, el sistema no se cae: muestra un aviso y deja el conteo manual.
- Muestra la imagen anotada junto al número contado y el nivel de confianza.

---

## 7. Carga y limpieza del Excel (`src/services/etl.py`)

El Excel tiene 240 filas y 10 columnas: `País_reportante, Flujo_comercial, Año, Código_SA6, Categoría_calzado, Socio_comercial, Valor_miles_USD, Cantidad_pares, Valor_USD, Valor_USD_por_par`.

Reglas, registrando cada una en `bitacora_limpieza`:
1. Validar tipos de datos y contar los valores faltantes (hoy hay 0).
2. Separar los registros con `Socio_comercial == "Mundo"` para no contarlos dos veces (hoy no hay ninguno; igual se informa).
3. **Claves repetidas:** si la combinación (Flujo_comercial, Año, Código_SA6, Socio_comercial) aparece más de una vez, se conserva la primera fila y las demás se marcan como `registro_valido = False`. Resultado esperado: **240 → 230 válidas, 10 descartadas**.
4. Validar la consistencia: `Valor_USD ≈ Valor_miles_USD × 1000` y `Valor_USD_por_par ≈ Valor_USD / Cantidad_pares` (tolerancia 0,01).
5. Las pruebas en `tests/test_etl.py` verifican estos totales sobre las filas válidas: importación **17.055,8 M USD** y exportación **10.605,5 M USD**.

---

## 8. Páginas

**Común a todas:** un login al entrar (`st.session_state`) y una barra lateral con el logotipo de texto "Manaco Data", el usuario, el rol y un botón para cerrar sesión. Cada rol ve solo sus páginas: el encargado ve apertura, ventas y cierre; gerencia ve inicio, historial y tablero; el administrador ve todo.

1. **Inicio (`app.py`).** Cuatro tarjetas KPI del día: pares en apertura, pares vendidos, cierres hechos o pendientes, y alertas activas. Debajo, la tabla de alertas pendientes y un gráfico de las diferencias de inventario de los últimos 30 días.
2. **Apertura.** Formulario con fecha, tienda, producto y saldo inicial (propone el cierre de ayer), más la tabla de aperturas del día. También permite abrir todos los productos de una tienda a la vez.
3. **Ventas.** Formulario rápido de venta, la tabla de ventas del día y, por cada producto, el stock disponible en tiempo real (saldo inicial − vendido).
4. **Cierre y conteo.** Se elige tienda, fecha y producto, y se muestran el saldo inicial, lo vendido y el esperado. Luego la foto (cámara o archivo), el conteo con IA, la corrección manual, el botón "Calcular y guardar cierre", y la alerta o confirmación con colores.
5. **Historial.** La planilla completa de cierres con filtros (fecha, tienda, producto, estado) y colores por estado. Se descarga en **Excel** con formato: encabezados en negrita, anchos ajustados y una hoja de resumen. Desde cada fila se puede ver la foto de evidencia.
6. **Tablero de mercado.** Con datos del Excel limpio:
   - Resumen de limpieza: filas originales, válidas y descartadas, y reglas aplicadas.
   - KPI: valor importado, valor exportado, saldo comercial, pares y valor por par.
   - **Gráfico 1:** importaciones frente a exportaciones por categoría, en barras agrupadas con la razón import./export. de cada una.
   - **Gráfico 2:** los 6 principales socios por valor, en dos paneles (proveedores y destinos).
   - **Gráfico 3:** valor por par por categoría (mínimo, mediana y máximo, con un punto y una línea).
   - Filtros por año, flujo, categoría y socio. Un selector de métrica "Valor USD / Cantidad de pares" muestra que las conclusiones cambian según lo que se mida.
   - Un cuadro de **limitaciones**: los datos son de España y no de Bolivia; el valor por par no es el precio al consumidor; la cobertura por año es desigual.
   - Una pestaña "Datos internos" con ventas por categoría de Manaco (de la base de datos), para mostrar la integración.
7. **Catálogo.** Alta, edición y baja de productos y tiendas.
8. **Usuarios.** Alta de usuarios y roles (solo el administrador).

---

## 9. Diseño visual (nivel profesional)

- Archivo `.streamlit/config.toml` con un tema claro: primaryColor `#B3261E` (rojo sobrio), fondo `#FAFAF9`, fondo secundario `#F1F0EE`, texto `#1C1B1F` y fuente sans serif.
- Tarjetas KPI propias en `src/ui/estilos.py`: borde suave, número grande, etiqueta pequeña y una variación con flecha.
- Gráficos Plotly con estilo uniforme: plantilla `simple_white`, un color de acento, el resto en gris, título que diga **la conclusión** (por ejemplo, "En deportivo se importa 3 veces lo que se exporta") y el formato numérico boliviano (miles con punto, decimales con coma).
- Mensajes claros con `st.success`, `st.warning` y `st.error`. Nunca debe aparecer un error técnico (*traceback*) al usuario.
- Fechas en formato `dd/mm/aaaa` y montos en Bs.
- Encabezado en cada página con un título, una línea que explique qué se hace ahí y un ícono.
- Diseño responsive, que funcione en una laptop y en el celular (para tomar la foto).

---

## 10. Etapas de trabajo

1. Estructura, entorno, `config.py`, `db.py` y modelos. Ejecuta `scripts/init_db.py`.
2. ETL del Excel y sus pruebas, con los totales de la sección 7.
3. Servicio de inventario y sus pruebas, incluido el ejemplo 50 → 12 → 38 → 36.
4. Login y páginas de apertura, ventas, cierre e historial.
5. Conteo por foto con YOLO-World y su respaldo manual.
6. Tablero de mercado y página de inicio.
7. `scripts/seed_demo.py`: 3 tiendas, 12 productos y 30 días de operación con algunas diferencias, para que la demo se vea con datos reales.
8. Revisión final: `pytest` en verde, `streamlit run app.py` sin errores y un recorrido por cada página. Corrige todo lo que falle.

---

## 11. README.md

Debe explicar:
- Qué es el sistema y qué problema de Manaco resuelve.
- Cómo instalarlo con Anaconda: `conda env create -f environment.yml`, `conda activate manaco`, `python scripts/init_db.py`, `python scripts/seed_demo.py`, `streamlit run app.py`.
- El usuario de prueba: `admin` / `manaco2026`, con la indicación de cambiarlo.
- Cómo funciona cada página.
- Un guion de demo de 2 minutos: apertura → venta → foto → alerta → historial → tablero.
- Las limitaciones y los próximos pasos.

---

## 12. Criterios de terminado

- [ ] `pytest` pasa todas las pruebas.
- [ ] El flujo apertura → ventas → cierre → alerta → historial funciona de principio a fin.
- [ ] El conteo por foto funciona, y si falla, el sistema sigue con el conteo manual.
- [ ] El tablero muestra 230 registros válidos y los 3 gráficos.
- [ ] Exportar a Excel funciona.
- [ ] Ninguna página muestra errores técnicos.
- [ ] El código está ordenado, comentado en español y sin archivos basura.

Cuando termines, muéstrame un resumen de lo construido y el comando exacto para abrir el sistema.
