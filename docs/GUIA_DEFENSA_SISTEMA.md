# Guía para defender Manaco Data

Esta guía describe **solo lo que existe en el código** (`app.py`, `pages/`, `src/`, `scripts/`). Cuando algo no está implementado, se dice con la etiqueta **No implementado**.

---

## 1. Qué es Manaco Data (en 5 líneas)

1. Manaco Data es una aplicación web local, hecha en Python con Streamlit, para la empresa boliviana de calzado Manaco.
2. Resuelve el **inventario sin control diario**: cada tienda registra la apertura (saldo inicial), las ventas y el cierre (conteo final) de pares.
3. El conteo del cierre se puede hacer con una **foto**: una IA (YOLO-World) cuenta los zapatos o las cajas, y la persona confirma o corrige.
4. El sistema compara lo contado con lo esperado (inicial − vendido) y genera **alertas** de faltante o sobrante.
5. También resuelve los **datos sin integrar**: limpia el Excel de comercio exterior de calzado y lo muestra en un tablero junto con las ventas internas.

---

## 2. Página por página

> Reglas comunes a todas las páginas:
> - Cada página llama a `proteger_pagina(...)`. Sin sesión iniciada, muestra "Inicie sesión…". Si el rol no tiene permiso, muestra "Su rol no tiene acceso a esta página".
> - Además, el menú lateral solo muestra las páginas permitidas para el rol.
> - Si una página falla de forma inesperada, se muestra un mensaje amable en lugar del error técnico, y el error queda en el registro (log).
> - Si no hay tiendas o productos activos, Apertura, Ventas y Cierre muestran "Primero registre tiendas y productos en el Catálogo" con un botón para ir al Catálogo.
> - Tras guardar algo, la página se recarga y muestra una notificación (toast) y un aviso de color.

### 2.1 Login (pantalla de ingreso)

**Para qué sirve:** identificar a la persona y su rol.

**Campos y botones:**
- **Usuario**: campo de texto.
- **Contraseña**: campo oculto.
- **Ingresar**: botón.
- Además se ven un panel rojo con el logo y 3 beneficios, que son solo decorativos.

**Validaciones:**
- El usuario se busca sin espacios y en minúsculas, así que `ADMIN` funciona igual que `admin`.
- La contraseña se compara con su **hash bcrypt**; nunca se guarda en texto plano.
- Si el usuario no existe, está **desactivado** o la contraseña no coincide, sale "Usuario o contraseña incorrectos." Es el mismo mensaje en los tres casos, para no revelar qué falló.

**Qué se guarda:** nada en la base. El usuario conectado (id, nombre, usuario, rol) queda en la sesión del navegador (`st.session_state`).

**No implementado:** recuperar la contraseña, bloquear la cuenta tras varios intentos fallidos y cerrar la sesión por inactividad.

**Frase para la defensa:** *"Las contraseñas se guardan cifradas con bcrypt, y el sistema muestra solo las páginas que corresponden al rol de cada usuario."*

### 2.2 Barra lateral (todas las páginas tras el login)

- Muestra el logo, el menú de las páginas permitidas y una tarjeta con el nombre, el usuario y el rol.
- El botón **Cerrar sesión** borra la sesión y vuelve al login.

### 2.3 Inicio (administrador y gerencia)

**Para qué sirve:** ver de un vistazo cómo va el inventario hoy en todas las tiendas.

**Qué muestra:**
- **Saludo** según la hora ("Buenos días/tardes/noches") y la fecha de hoy.
- **4 tarjetas KPI**, cada una con un minigráfico de los últimos 7 días:
  - *Pares en apertura*: suma de los saldos iniciales de hoy, con la variación frente a ayer.
  - *Pares vendidos*: pares vendidos hoy y su importe en Bs.
  - *Cierres del día*: hechos / total de aperturas de hoy, y cuántos faltan cerrar.
  - *Alertas activas*: cierres con diferencia que nadie revisó todavía; tiene un punto rojo que pulsa si hay alertas.
- **Alertas pendientes**: las 5 más recientes, cada una con su mensaje, su diferencia y su tienda.
  - Expander **Ver todas (N)**: tabla con todas las alertas.
  - Lista **Marcar como revisadas**, para elegir una o varias.
  - Botón **Marcar como revisadas**, desactivado si no se eligió ninguna.
- **Dona** "X % de los cierres cuadran", con los últimos 30 días.
- **Tiendas con más diferencias**: ranking de las 5 tiendas con más pares descuadrados en 30 días.
- **Gráfico de diferencias**: faltantes y sobrantes por día en los últimos 30 días.

**Validaciones:** el bloque para marcar alertas aparece solo para administrador o gerencia.

**Qué se guarda:** al marcar revisadas, el campo `alerta_atendida = True` en la tabla `cierres`. La alerta no se borra: el cierre sigue en el historial.

**Frase para la defensa:** *"Gerencia ve aquí cada mañana qué tienda tiene faltantes. Cuando revisa una alerta la marca como atendida, pero el cierre queda en el historial."*

### 2.4 Apertura (administrador y encargado)

**Para qué sirve:** registrar el **saldo inicial** de pares de cada producto al abrir la tienda.

**Campos arriba:**
- **Fecha**: por defecto hoy, en formato dd/mm/aaaa.
- **Tienda**: el sistema recuerda la última tienda elegida.

**Pestaña "Un producto":**
- **Producto**: lista con código, nombre, talla y color.
- Si ayer hubo cierre, aparece la sugerencia "Se propone el conteo del cierre de ayer: N pares", y ese valor viene escrito en el campo.
- **Saldo inicial (pares)**: número entero, mínimo 0.
- Botón **Registrar apertura**.
- Si el producto ya tiene apertura ese día, en lugar del formulario sale un aviso con su saldo.

**Pestaña "Toda la tienda":**
- Tabla editable con los productos **pendientes** de abrir. La columna *Saldo inicial* viene con el cierre de ayer (o 0) y se puede cambiar.
- Botón **Abrir N productos de [tienda]**.
- Si ya están todos abiertos, se muestra un estado vacío.

**Tabla final:** las aperturas de esa fecha y tienda, con la hora de registro y el total de pares.

**Validaciones** (en `src/services/inventario.py`):
- El saldo inicial no puede ser negativo ("El saldo inicial no puede ser negativo.").
- No puede haber **dos aperturas** del mismo producto, tienda y fecha. Lo controlan el código y una restricción `UNIQUE` en la base.
- "Abrir toda la tienda" salta los productos que ya estaban abiertos y lo informa.

**Qué se guarda:** una fila en `aperturas` con fecha, tienda, producto, saldo_inicial, usuario y hora de creación.

**No implementado:** editar o borrar una apertura ya registrada.

**Frase para la defensa:** *"El saldo inicial de hoy se propone a partir del conteo de cierre de ayer, así el encargado no escribe de memoria. Y no se puede abrir dos veces el mismo producto el mismo día."*

### 2.5 Ventas (administrador y encargado)

**Para qué sirve:** registrar cada venta y ver el stock disponible en tiempo real.

**Qué muestra y qué se puede hacer:**
- **Campos arriba:** Fecha y Tienda.
- **3 KPI:** pares vendidos hoy, importe del día en Bs y stock disponible total.
- **Nueva venta:**
  - **Producto**: solo aparecen los productos **abiertos y todavía no cerrados**.
  - Una sugerencia muestra el disponible y el precio de lista.
  - **Cantidad (pares)**: mínimo 1.
  - **Precio unitario (Bs)**: viene con el precio de lista y se puede cambiar, por ejemplo para un descuento.
  - Botón **Registrar venta**.
- **Stock disponible:** barras por producto. Verde si queda más del 50 % del saldo inicial, amarillo entre 20 y 50 %, rojo por debajo del 20 %.
- **Tabla "Ventas del [fecha]":** hora, código, producto, categoría, cantidad, precio e importe.

**Validaciones:**
- La cantidad debe ser mayor que 0.
- **No hay venta sin apertura**: "No hay apertura de X… Registre primero la apertura."
- **No se vende** un producto que **ya tiene cierre** ese día.
- **No se vende más del stock**: "No hay stock suficiente de X: disponible 38, se intentó vender 40."
- El precio no puede ser negativo.
- Si la tienda no tiene aperturas ese día, sale un estado vacío con el botón "Ir a Apertura".

**Qué se guarda:** una fila en `ventas` con fecha, **hora automática**, tienda, producto, cantidad, precio unitario y usuario.

**No implementado:**
- Editar o anular una venta.
- Conectar con una caja o punto de venta: las ventas se escriben a mano.

**Frase para la defensa:** *"El stock disponible es el saldo inicial menos lo vendido y se actualiza al instante. El sistema no deja vender lo que no hay."*

### 2.6 Cierre y conteo (administrador y encargado)

**Para qué sirve:** contar el stock al final del día (con foto o a mano), compararlo con lo esperado y generar la alerta.

Funciona como un **asistente en 3 pasos**, con un indicador arriba: Seleccionar → Contar → Resultado.

**Paso 1 – Seleccionar:**
- **Campos:** Fecha, Tienda y Producto. Solo aparecen los productos con apertura ese día.
- **3 KPI:** Saldo inicial, Vendido hoy y **Saldo esperado** (inicial − vendido).
- Si no hay aperturas, sale "no se puede cerrar sin apertura" y el botón "Ir a Apertura".

**Paso 2 – Contar** (solo si el producto todavía no tiene cierre):
- **Origen de la foto**: *Subir archivo* (JPG, JPEG, PNG o WEBP) o *Cámara* (la del celular o la de la laptop).
- **¿Qué se cuenta?**: *Pares* (zapatos sueltos ÷ 2) o *Cajas* (1 caja = 1 par).
- **Umbral de confianza**: control deslizante de 0,05 a 0,90, por defecto 0,25. Más bajo detecta más objetos, pero también más errores.
- Botón **Contar con IA**: aparece solo cuando hay una foto. Muestra la foto original, la foto con recuadros numerados y un número grande con el conteo, la confianza y los objetos detectados.
- **Conteo final (pares)**: viene con el valor de la IA y **se puede corregir**. Se guardan los dos valores.
- **Observación (opcional)**: texto libre, por ejemplo "Posible venta no registrada".
- Botón **Calcular y guardar cierre**.

**Paso 3 – Resultado** (si el producto ya tiene cierre):
- Tarjeta grande con el estado y el mensaje, por ejemplo **"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"**, más los bloques Esperado, Contado y Diferencia.
- Conteo IA con su confianza, conteo final, observación y la foto de evidencia (o "sin foto").
- **Solo el administrador** ve el expander **Anular cierre**: campo *Motivo de la anulación* y botón **Anular cierre**.

**Validaciones:**
- No se guarda si el conteo final está vacío ("Ingrese el conteo final antes de guardar.") o es negativo.
- **No hay cierre sin apertura.**
- **Un cierre no se repite**: "ya fue guardado. Solo el administrador puede anularlo." Hay además una restricción `UNIQUE` en la base.
- Si la imagen no se puede leer: "No se pudo leer la imagen…".
- Si la IA no está disponible o falla, sale un aviso amarillo y se cuenta a mano (ver sección 4).
- Si no se detecta ningún objeto: "No se detectaron objetos. Baje el umbral o cuente manualmente."
- Si no se puede guardar la foto en el disco: mensaje de error y el cierre no se guarda.
- Para anular hacen falta el rol administrador y un motivo; se comprueba también en el servicio, no solo en la pantalla.

**Cálculo** (en `inventario.py`):
- Saldo esperado = saldo inicial − total vendido.
- Diferencia = conteo final − saldo esperado.
- Estado: **Correcto** si |diferencia| ≤ tolerancia (0 por defecto, en `src/config.py`), **Faltante** si la diferencia es negativa, **Sobrante** si es positiva.

**Qué se guarda:**
- En `cierres`: saldo_inicial, total_vendido, saldo_esperado, conteo_ia, confianza_ia, conteo_final, diferencia, estado, foto_ruta, observación, usuario y `alerta_atendida`. Esta última vale True si el estado es Correcto y False si hay diferencia, que es lo que crea la alerta.
- La foto original se guarda en `data/fotos/AAAA-MM-DD_tienda_producto.jpg`.
- Al **anular**, se copia el cierre a `anulaciones_cierre` (con el motivo, quién anuló y cuándo) y se borra de `cierres`, así se puede cerrar de nuevo.

**Frase para la defensa:** *"La IA propone el conteo, pero la persona tiene la última palabra. Guardamos los dos números y la foto como evidencia, y el cierre no se puede repetir: solo el administrador lo anula, con un motivo que queda registrado."*

### 2.7 Historial (administrador y gerencia)

**Para qué sirve:** consultar, filtrar y descargar todos los cierres.

**Qué muestra y qué se puede hacer:**
- **Filtros:**
  - *Rango de fechas*: por defecto los últimos 30 días que tienen datos.
  - *Tienda*, *Producto* y *Estado*: se puede elegir más de uno; vacío significa "todos".
- **4 KPI:** cierres del período, % correctos, pares faltantes y pares sobrantes.
- **Planilla de cierres:** el estado va coloreado (verde, rojo o naranja) y la diferencia se muestra en rojo si es negativa y en ámbar si es positiva.
- **Seleccionar una fila** abre el detalle: estado, foto de evidencia y confianza de la IA, o "se registró sin foto".
- Botón **Descargar Excel**:
  - Crea el archivo `cierres_manaco_AAAAMMDD_AAAAMMDD.xlsx` con lo que está filtrado.
  - Hoja **Cierres**, con colores por estado, autofiltro y encabezado fijo.
  - Hoja **Resumen**, con totales por estado y por tienda.

**Validaciones:**
- Si no hay cierres, sale un estado vacío con el botón "Ir a Cierre y conteo".
- Si los filtros no dan resultados: "Ningún cierre coincide…".
- Si la foto ya no existe en el disco, se avisa en lugar de dar error.

**Qué se guarda:** nada; esta página es solo de lectura.

**Frase para la defensa:** *"Gerencia puede filtrar, por ejemplo, solo los faltantes de una tienda, ver la foto que lo respalda y llevarse un Excel con resumen para su reunión."*

### 2.8 Tablero de mercado (administrador y gerencia)

**Para qué sirve:** analizar el comercio exterior de calzado (Excel limpio) junto con las ventas de Manaco.

**Pestaña "Mercado":**
- **Filtros:**
  - *Año*, *Flujo* (Importación/Exportación), *Categoría* y *Socio*: se puede elegir más de uno.
  - *Métrica*: Valor USD o Cantidad de pares.
- **Banner con 4 KPI:** importado (M USD), exportado (M USD), saldo comercial (déficit o superávit) y pares en millones con el valor por par.
- **3 gráficos**, cada uno con un título que dice la conclusión:
  1. Importación frente a exportación por categoría, por ejemplo "En X se importa N veces más…".
  2. Principales proveedores y destinos (top 6).
  3. Valor por par por categoría: mediana, mínimo y máximo.
- **Nota "Limitaciones de estos datos":**
  - El país reportante es España, no Bolivia.
  - El valor por par es aduanero, no el precio al público.
  - La cobertura por año es desigual.
  - Solo incluye 30 socios.

**Pestaña "Datos internos":**
- 3 KPI de las ventas de Manaco: ventas totales en Bs, pares vendidos y precio medio por par.
- Gráfico de ventas por categoría.
- Tabla **Cruce**: une por categoría (código SA6) los pares, las ventas en Bs y el precio medio de Manaco con la importación de España y la mediana del mercado en US$ por par.

**Pestaña "Limpieza de datos":**
- Flujo **240 filas → 240 válidas / 0 descartadas**.
- Línea de tiempo de las reglas aplicadas, leída de `bitacora_limpieza`.
- Tabla de las **20 filas con clave repetida**: comparten flujo, año, código SA6 y socio, pero tienen valores distintos. Se marcan y se conservan.
- **Diccionario de datos**: las 10 columnas del Excel con su tipo, significado, valores observados y faltantes (`src/services/diccionario.py`).
- Botón **Descargar tabla depurada (Excel)**: hojas *Tabla depurada* (240 filas con la marca de clave repetida), *Claves repetidas*, *Diccionario* y *Bitácora*.

**Qué se guarda:** nada; esta página es solo de lectura. Los datos se cargan con `scripts/init_db.py`.

**No implementado:** subir otro Excel desde la página. Para recargar el Excel hay que ejecutar `python scripts/init_db.py`.

**Frase para la defensa:** *"Por categoría, el orden es el mismo en valor y en pares; pero por socio cambia: República Checa entra al top 6 de proveedores por pares y no por valor, porque vende el calzado más barato. Por eso el tablero deja elegir la métrica, y además avisamos las limitaciones de los datos."*

### 2.9 Catálogo (solo administrador)

**Pestaña "Productos":**
- **Fichas** de todos los productos, con código, nombre, categoría, talla, color y precio. Las fichas de los productos dados de baja se ven apagadas.
- **Editar productos:** tabla editable.
  - Se pueden cambiar Nombre, Categoría (lista: Deportivo, Caucho y cuero, Cuero), Talla, Color, Precio, Costo y **Activo**.
  - Los campos Código y SA6 están bloqueados; el SA6 se calcula solo a partir de la categoría.
  - Botón **Guardar cambios de productos**.
- **Nuevo producto:**
  - Campos: Código de modelo (se pasa a MAYÚSCULAS), Nombre, Categoría, Talla, Color, Precio de venta y Costo.
  - Botón **Agregar producto**.

**Pestaña "Tiendas":**
- Fichas de las tiendas con nombre, tipo y ciudad.
- **Editar tiendas:**
  - Se pueden cambiar Nombre, Ciudad (lista de 8 ciudades), Tipo (tienda o almacén) y Activo.
  - Botón **Guardar cambios de tiendas**.
- **Nueva tienda:** campos Nombre, Ciudad y Tipo, más el botón **Agregar tienda**.

**Validaciones:**
- El código y el nombre del producto son obligatorios.
- No se repite el código de producto ("Ya existe un producto con el código…").
- Precio y costo deben ser ≥ 0.
- El nombre de la tienda es obligatorio y no se repite.
- Si en la edición se deja vacío el nombre de un producto, se conserva el anterior.

**Qué se guarda:** filas en `productos` y `tiendas`.
- **La baja no borra:** solo pone `activo = False`. Así el historial se mantiene y el producto o la tienda dejan de aparecer en los selectores.

**No implementado:** borrar definitivamente productos o tiendas, y cambiar el código de un producto ya creado.

**Frase para la defensa:** *"Dar de baja no borra nada: el producto deja de aparecer para vender, pero sus cierres antiguos siguen en el historial."*

### 2.10 Usuarios (solo administrador) — ver el detalle en la sección 3

> **Páginas 2.11 a 2.13:** las agregó un compañero (pull request #1) y usan **datos simulados**, marcados en pantalla como **[Simulado]** y **[Supuesto]**. No son ventas ni producción reales de Manaco: dígalo así en la defensa.

### 2.11 Pronóstico de demanda (administrador y gerencia)

**Para qué sirve:** proyectar cuántos pares por mes venderá cada línea, con y sin el efecto del mercado informal (contrabando).

**Campos:**
- **Línea**: Deportivo, Caucho y cuero o Cuero.
- **Meses de historial**: 12, 24 o 36.
- **Meses a proyectar**: 3, 6 o 12.

**Qué muestra:**
- **4 KPI:** pronóstico sin ajuste del próximo mes, pronóstico ajustado, sensibilidad de la línea al mercado informal y error del ajuste (**MAPE**), comparado con el error sin ajustar.
- **Gráfico:** historial y proyección.
- **Tabla de detalle:** mes, pronóstico sin ajustar, pronóstico ajustado y presión informal proyectada.
- **Nota "De dónde salen estos datos".**

**Cómo calcula** (`src/services/pronostico.py`):
- **Historial:** se **simula** en el momento, porque el sistema solo tiene 30 días de ventas. Incluye un nivel base por línea, estacionalidad (inicio de clases y fin de año) y una presión informal creciente.
- **Pronóstico sin ajustar:** promedio móvil estacional.
- **Pronóstico ajustado:** reconstruye la demanda real (ventas ÷ efecto informal) y le vuelve a aplicar la presión informal proyectada.
- **Backtest:** compara el error (MAPE) de los dos métodos en los últimos 6 meses conocidos.
- **Sensibilidad por línea:** es un **supuesto** del equipo: 0,35 en Deportivo, 0,20 y 0,10 en las otras dos.

**Qué se guarda:** nada; esta página es solo de cálculo. No necesita `seed_solucion.py`.

**Frase para la defensa:** *"Mostramos el método: si el contrabando reduce las ventas, un pronóstico que lo ignora sobreestima la demanda. Los datos son simulados, porque no hay 24 meses de historia real, así que el MAPE demuestra que el método funciona, no cuánto pesa el contrabando en la realidad."*

### 2.12 Prototipo de escenario (administrador y gerencia)

**Para qué sirve:** simular un escenario de mercado ("¿qué pasa si sube el dólar paralelo o crece el contrabando?") y ver cómo cambian 5 indicadores.

**Campos:**
- **Línea**.
- **Tipo de cambio paralelo (Bs/USD)**: de 6,96 a 15.
- **Presión del mercado informal**: de 0 a 0,95.

**Qué muestra:**
- **Cómo se calculan dos de ellos:** la *brecha* compara cada línea con calzado informal equivalente (el descuento informal promedio aplicado a su precio) y baja si sube el dólar paralelo; la *cobertura* compara la producción simulada, calibrada con la demanda base de cada línea, con la demanda proyectada del escenario.
- **5 KPI frente a metas de referencia.** Se ponen en rojo si no cumplen la meta. Las metas son un **supuesto** del equipo, no metas oficiales:
  - ventas proyectadas, contra el promedio de los últimos 12 meses;
  - cobertura de producción (meta ≥ 100 %);
  - tasa de defectos (meta ≤ 3 %);
  - brecha de precio frente al mercado informal (meta ≤ 20 %);
  - rechazo en la ingesta de datos (meta ≤ 3 %).
- **Gráfico de demanda proyectada**, con el escenario elegido.
- **Resumen por línea:** pronóstico a 6 meses y MAPE.
- **Referencia externa:** el gráfico de valor por par del Excel de España, que sí son datos reales del archivo.
- **Estado de ingesta por sucursal:** las últimas cargas, con filas leídas, corregidas y rechazadas.

**Validación:** si no están cargados los datos simulados, la página muestra "No hay datos simulados del escenario. Ejecute python scripts/seed_solucion.py."

**Qué se guarda:** nada; esta página lee las tablas simuladas (ver la sección 6).

**Frase para la defensa:** *"Si sube el dólar paralelo, el calzado informal, que se compra en dólares, se encarece en bolivianos y la brecha de Manaco se reduce; si sube la presión informal, baja la demanda proyectada y mejora la cobertura de producción. Es un prototipo de decisión con datos simulados."*

### 2.13 Entregables escritos (administrador y gerencia)

**Para qué sirve:** mostrar dentro del sistema los 4 textos que pide la rúbrica del caso. Es una página de **solo texto**: no tiene campos ni guarda nada.

**Pestañas:**
1. **Problemas prioritarios:** tabla con 5 problemas, su justificación y los datos que usa el sistema.
2. **Síntesis ejecutiva:** 3 hallazgos, 2 limitaciones, 1 pregunta estratégica y las respuestas a las 5 preguntas de referencia del caso.
3. **Ficha de una página:** la propuesta estratégica.
4. **Recomendación ejecutiva:** 2 alternativas comparadas y 3 indicadores de seguimiento.

El mismo contenido está en `docs/ENTREGABLES_ESCRITOS.md` y en el Word `docs/Solucion_Manaco_Data.docx`, que se genera con `scripts/generar_docx_solucion.py`.

**Frase para la defensa:** *"Los entregables escritos usan las mismas cifras que calcula el sistema, por ejemplo la alerta de 'Faltan 2 pares' y las 240 filas válidas del Excel."*

---

## 3. Roles: qué puede hacer cada uno

Los permisos están en `PERMISOS`, dentro de `src/config.py`:

| Página | Administrador | Encargado | Gerencia |
| --- | :---: | :---: | :---: |
| Inicio | ✅ | ❌ | ✅ |
| Apertura | ✅ | ✅ | ❌ |
| Ventas | ✅ | ✅ | ❌ |
| Cierre y conteo | ✅ | ✅ | ❌ |
| Historial | ✅ | ❌ | ✅ |
| Tablero de mercado | ✅ | ❌ | ✅ |
| Pronóstico de demanda | ✅ | ❌ | ✅ |
| Prototipo de escenario | ✅ | ❌ | ✅ |
| Entregables escritos | ✅ | ❌ | ✅ |
| Catálogo | ✅ | ❌ | ❌ |
| Usuarios | ✅ | ❌ | ❌ |

**Administrador:**
- Ve las 11 páginas.
- Es el **único que puede anular un cierre**, con motivo.
- Maneja el catálogo y los usuarios.
- Puede marcar alertas como revisadas.
- Al entrar, aparece en **Inicio**.

**Encargado:**
- Trabaja en la tienda: Apertura, Ventas y Cierre y conteo.
- No ve Inicio, alertas, historial ni tablero.
- No puede anular cierres: no ve el botón, y el servicio también lo rechaza.
- Al entrar, aparece en **Apertura**, la primera de sus páginas.

**Gerencia:**
- Solo consulta: Inicio, Historial, Tablero, Pronóstico de demanda, Prototipo de escenario y Entregables escritos.
- Puede **marcar alertas como revisadas** en Inicio.
- No registra aperturas, ventas ni cierres.

### Todo lo que se puede hacer en la página Usuarios

1. **Ver todos los usuarios** en fichas con iniciales, nombre, usuario, rol con color y estado (las cuentas inactivas se ven apagadas). Arriba hay un resumen de lo que ve cada rol.
2. **Editar usuarios** en una tabla:
   - Se pueden cambiar **Nombre**, **Rol** (administrador, encargado o gerencia) y **Activo**.
   - Los campos *Usuario* y *Creado* están bloqueados: el nombre de ingreso no se puede cambiar.
   - Botón **Guardar cambios**.
   - **Protección:** el administrador **no puede quitarse a sí mismo** el rol de administrador **ni desactivar su propia cuenta**. Sale un error y no se guarda nada.
   - Un usuario desactivado ya **no puede ingresar**: el login lo rechaza.
3. **Crear un usuario:**
   - Campos: *Nombre completo*, *Usuario (para ingresar)*, *Rol* (por defecto encargado) y *Contraseña*.
   - Botón **Crear usuario**.
   - Validaciones (en `src/auth.py`):
     - Nombre y usuario obligatorios.
     - El usuario se guarda en minúsculas y sin espacios.
     - El rol debe ser válido.
     - Contraseña de **mínimo 6 caracteres**.
     - El usuario no puede repetirse.
   - La contraseña se guarda como **hash bcrypt**.
4. **Cambiar contraseña:**
   - Se elige el *Usuario* y se escriben *Nueva contraseña* y *Repita la contraseña*.
   - Botón **Actualizar contraseña**.
   - Validaciones: mínimo 6 caracteres y las dos deben coincidir.
   - Sirve para cualquier usuario, incluido el propio, y **no pide la contraseña anterior**, porque lo hace el administrador.

**No implementado en Usuarios:**
- Borrar usuarios definitivamente (solo se desactivan).
- Que cada usuario cambie su propia contraseña desde su perfil.
- Comprobar que el nombre no quede vacío al editar.
- Cerrar al momento la sesión de un usuario que ya está conectado cuando se lo desactiva: su sesión sigue hasta que la cierre, y lo que se le niega es volver a ingresar.

---

## 4. Conteo por foto (IA)

**Modelo:**
- Usa **YOLO-World** de Ultralytics, con los pesos `yolov8s-world.pt`.
- Los pesos se guardan en `data/modelos/`, junto con el modelo de texto **CLIP** que el detector necesita.
- Se descargan una sola vez: unos 25 MB los pesos y unos 340 MB CLIP.
- Se carga una sola vez por servidor (`st.cache_resource`).

**Qué detecta:**
- YOLO-World es un detector de **vocabulario abierto** (*zero-shot*): se le dicen las clases en texto, sin entrenarlo con fotos de Manaco.
- Las clases están en `src/config.py` (`CLASES_YOLO`): **"shoe"** (zapato) y **"shoe box"** (caja de zapatos).
- Se cuentan solo las detecciones con confianza ≥ al umbral, que por defecto es 0,25 y se puede mover en pantalla.

**Cómo convierte zapatos en pares:**
- **Modo Pares**: se cuentan los objetos "shoe" y se aplica `pares = (zapatos + 1) // 2`, es decir, la mitad redondeada hacia arriba. Por ejemplo, 7 zapatos dan 4 pares y 8 zapatos dan 4 pares.
- **Modo Cajas**: se cuentan los objetos "shoe box"; 1 caja equivale a 1 par.
- La confianza que se muestra es el **promedio** de las detecciones.
- La foto se gira según sus datos EXIF (fotos de celular) y se dibujan recuadros rojos numerados en el orden en que se leen, de arriba abajo y de izquierda a derecha.

**Qué pasa si falla:**
- **Si el modelo no carga** (sin internet la primera vez o archivos dañados), `modelo_disponible()` devuelve el aviso "El conteo automático no está disponible (…). Use el conteo manual."
- **Si la predicción falla**, se lanza `ErrorVision` y sale "No se pudo analizar la foto… Ingrese el conteo manualmente."
- **Si detecta 0 objetos**, sale "No se detectaron objetos. Baje el umbral o cuente manualmente."
- **Si la foto no es una imagen válida**, sale "No se pudo leer la imagen…".
- **En todos los casos el sistema sigue funcionando**: el campo *Conteo final* se llena a mano y el cierre se guarda con `conteo_ia` vacío.
- La persona **siempre puede corregir** el número de la IA. Se guardan el conteo de la IA y el conteo final.

**Limitación:** funciona mejor con zapatos o cajas separados, buena luz y vista de frente. Con pilas apretadas conviene contar cajas o corregir a mano.

---

## 5. Limpieza del Excel

**Archivo y proceso:**
- Archivo: `data/raw/Base_de_Datos_MANACO.xlsx`, con 10 columnas.
- Lo procesa `src/services/etl.py` cuando se ejecuta `python scripts/init_db.py`.
- Primero se comprueba que estén las 10 columnas; si falta alguna, se detiene con un error que dice cuáles faltan.
- Las filas **no se borran**: cada una queda marcada con `registro_valido` True o False.
- Cada regla se anota en `bitacora_limpieza`.

| # | Regla | Qué hace | Filas afectadas |
| --- | --- | --- | --- |
| 1 | Validación de tipos y faltantes | Quita espacios en los textos, convierte a número los años, códigos, pares y valores, y cuenta los vacíos. Una fila con algún vacío queda inválida. | **0** |
| 2 | Separación de socio "Mundo" | Marca como inválidas las filas con socio "Mundo", porque son un total y se contarían dos veces. | **0** (no hay "Mundo") |
| 3 | Claves repetidas | Clave = Flujo + Año + Código SA6 + Socio. Las filas que comparten clave tienen valores distintos (pueden ser registros parciales de la fuente), así que se **marcan y se conservan** para validarlas con la fuente original. | **20** marcadas, 0 descartadas |
| 4 | Consistencia de valores | Verifica que `Valor_USD ≈ Valor_miles_USD × 1000` y que `Valor_USD_por_par ≈ Valor_USD / Cantidad_pares`, con una tolerancia de 0,01. | **1** inconsistencia (en Valor_USD vs. miles), **0** en valor por par |
| — | Resumen | Totaliza el resultado. | **240 → 240 válidas, 0 descartadas** |

> **Importante y honesto:** la regla 4 solo **informa** la inconsistencia en la bitácora; **no marca la fila como inválida**. Como las claves repetidas tampoco se descartan, las 240 filas quedan válidas.

**Datos que quedan:**
- País reportante: España.
- Años: 2020 a 2024, con 28, 34, 46, 50 y 82 registros.
- 30 socios comerciales y 3 códigos SA6: 640411 Deportivo, 640399 Caucho y cuero, 640420 Cuero.

---

## 6. Tablas de la base de datos

La base es **SQLite**, en el archivo `data/manaco.db`, y se usa con SQLAlchemy 2. Las claves foráneas están activadas.

| Tabla | Qué guarda |
| --- | --- |
| `usuarios` | id, nombre, usuario (único), hash_contrasena (bcrypt), rol, activo, creado_en |
| `tiendas` | id, nombre (único), ciudad, tipo (tienda/almacén), activo |
| `productos` | id, codigo_modelo (único), nombre, categoria, codigo_sa6, talla, color, precio_venta_bs, costo_bs, activo |
| `aperturas` | fecha, tienda, producto, saldo_inicial, usuario, creado_en. **Única** por fecha + tienda + producto |
| `ventas` | fecha, hora, tienda, producto, cantidad, precio_unitario_bs, usuario |
| `cierres` | fecha, tienda, producto, saldo_inicial, total_vendido, saldo_esperado, conteo_ia, conteo_final, diferencia, estado, foto_ruta, confianza_ia, observacion, alerta_atendida, usuario, creado_en. **Única** por fecha + tienda + producto |
| `anulaciones_cierre` | Auditoría: datos del cierre anulado (fecha, tienda, producto, conteo, diferencia, estado), motivo, quién anuló y cuándo |
| `comercio_exterior` | Las 240 filas del Excel (país, flujo, año, SA6, categoría, socio, valores, pares, valor por par) y `registro_valido` |
| `bitacora_limpieza` | Cada regla de limpieza: regla, filas_afectadas, detalle, fecha |

**Tablas de datos simulados**, agregadas con el pronóstico y el prototipo. Las llena `scripts/seed_solucion.py` con 24 meses de datos **[Simulado]**:

| Tabla | Qué guarda |
| --- | --- |
| `dim_fecha` | Calendario: fecha, año, mes, si es inicio de clases y si es feriado |
| `fact_produccion` | Lotes de producción: fecha, lote, producto, pares, costo de insumos y de mano de obra |
| `fact_calidad` | Incidencias de calidad por lote: defectos, devoluciones y motivo |
| `ref_mercado_local` | Precio de la competidora informal y tipo de cambio paralelo por ciudad y mercado (Eloy Salmón, La Cancha, La Ramada) |
| `log_ingesta` | Cargas de archivos por sucursal: filas leídas, corregidas y rechazadas |

Por eso el esquema se llama "en estrella": tablas de hechos (`fact_…`) alrededor de dimensiones como la fecha y el producto.

Las **alertas no son una tabla aparte**: son los cierres con estado distinto de Correcto y `alerta_atendida = False`.

---

## 7. Guion de demo de 2 minutos (datos concretos)

**Antes de la defensa:**
1. Prepare los datos, en la carpeta del proyecto y con el entorno activado (`.venv` o `conda activate manaco`):
   ```
   python scripts\seed_demo.py
   python scripts\seed_solucion.py
   streamlit run app.py
   ```
2. `seed_demo` carga 3 tiendas, 12 productos y 30 días de operación **hasta ayer**, así que **hoy queda libre** para la demo.
   ⚠️ `seed_demo` **borra** los datos [Simulado] de producción y calidad: si no corre después `seed_solucion`, el *Prototipo de escenario* queda vacío en plena defensa.
3. Tenga a mano una foto con varios zapatos sueltos, por ejemplo 4 zapatos, que son 2 pares.
4. Ingrese con **admin / manaco2026**.

| Tiempo | Paso | Qué hacer y qué escribir | Qué decir |
| --- | --- | --- | --- |
| 0:00 | **Inicio** | Muestre los 4 KPI, las alertas de la última semana y la dona. | "Gerencia ve aquí los faltantes de cada tienda." |
| 0:15 | **Apertura (un producto)** | Fecha: hoy. Tienda: **Tienda Prado**. Pestaña *Un producto* → **MAN-DEP-001 · Zapatilla Runner Pro**. Aparece la sugerencia del cierre de ayer; cambie el saldo a **50** → *Registrar apertura*. | "El sistema propone el cierre de ayer." |
| 0:30 | **Apertura (toda la tienda)** | Pestaña *Toda la tienda* → botón **Abrir 11 productos de Tienda Prado**. | "Abrimos el resto en un clic." |
| 0:40 | **Venta** | *Ventas* → Tienda Prado → producto **MAN-DEP-001**, cantidad **12**, precio sin cambiar (**389**) → *Registrar venta*. El disponible baja a **38**. | "El stock baja al instante." |
| 0:55 | **Venta inválida** | Mismo producto, cantidad **40** → *Registrar venta*. Sale "No hay stock suficiente… disponible 38, se intentó vender 40." | "No deja vender lo que no hay." |
| 1:05 | **Foto** | *Cierre y conteo* → Tienda Prado → **MAN-DEP-001**. Se ven inicial **50**, vendido **12** y esperado **38**. Suba la foto → *Contar con IA* → recuadros, conteo y confianza. | "La IA cuenta zapatos y los divide entre 2." |
| 1:25 | **Alerta** | En *Conteo final* escriba **36**; observación: "Posible venta no registrada" → *Calcular y guardar cierre*. Sale la tarjeta roja **"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"**. | "La persona confirma o corrige; guardamos los dos números y la foto." |
| 1:40 | **Historial** | Filtro *Estado* = **Faltante** → seleccione la fila de hoy y se ve la foto → *Descargar Excel*. | "Evidencia y reporte para gerencia." |
| 1:50 | **Tablero** | Muestre **240 → 240**, las 20 claves repetidas y el diccionario en *Limpieza de datos*, descargue la tabla depurada, y cambie la *Métrica* a **Cantidad de pares** en *Mercado*. | "Por socio, la métrica cambia el ranking; y avisamos las limitaciones." |

**Si sobra tiempo:**
- Ingrese como **encargado / manaco2026** para mostrar que solo ve Apertura, Ventas y Cierre.
- Vuelva al cierre de MAN-DEP-001 como admin para mostrar *Anular cierre* con su motivo.

**Si la IA no responde:** diga "si la IA falla, el sistema sigue con el conteo manual", escriba 36 y continúe.

---

## 8. 21 preguntas probables del docente

1. **¿Cómo se calcula la diferencia?** Saldo esperado = inicial − vendido; diferencia = conteo final − esperado. Si es negativa es faltante, si es positiva es sobrante, y si es 0 (o está dentro de la tolerancia) es correcto.
2. **¿Qué pasa si intento vender sin apertura o más de lo que hay?** El servicio lo rechaza con un mensaje claro y no guarda nada.
3. **¿Se puede cerrar dos veces el mismo producto?** No. El código lo impide y además hay una restricción UNIQUE en la base. Solo el administrador puede anularlo, con motivo, y eso queda en `anulaciones_cierre`.
4. **¿Qué modelo de IA usan y por qué?** YOLO-World, un detector *zero-shot* que reconoce "shoe" y "shoe box" a partir de un texto, sin entrenarlo con fotos propias.
5. **¿Cómo pasan de zapatos a pares?** Zapatos ÷ 2, redondeando hacia arriba. En modo cajas, 1 caja = 1 par.
6. **¿Y si la IA se equivoca?** La persona corrige el número. Se guardan el conteo de la IA, el conteo final, la confianza y la foto.
7. **¿Y si no hay internet o el modelo falla?** Aparece un aviso y se cuenta a mano; el sistema no se cae.
8. **¿Cómo guardan las contraseñas?** Con un hash bcrypt (con *salt*); nunca en texto plano.
9. **¿Cómo controlan los permisos?** Con un diccionario de permisos por rol. El menú solo muestra lo permitido y cada página vuelve a comprobarlo al abrirse.
10. **¿Qué limpieza le hicieron al Excel?** Cuatro reglas: tipos y faltantes (0), socio "Mundo" (0), claves repetidas (20 filas marcadas y conservadas) y consistencia (1 inconsistencia, solo informada). Las 240 filas quedan válidas, y el tablero muestra el diccionario de datos y permite descargar la tabla depurada.
11. **¿Por qué no descartan las claves repetidas?** Porque las filas que comparten clave tienen valores distintos: pueden ser registros parciales de la fuente y no copias. Descartarlas a ciegas perdería información; se marcan para validarlas con la fuente original, y se ven en la pestaña de limpieza y en la hoja *Claves repetidas* del Excel descargable. Los hallazgos se mantienen igual con o sin esas filas.
12. **¿Cómo integran los datos internos con el mercado?** Cada categoría de producto tiene su código SA6, el mismo del Excel. La tabla *Cruce* une las ventas de Manaco con la importación por ese código.
13. **¿Qué limitaciones tienen los datos de mercado?** Son de España y no de Bolivia, el valor por par es aduanero y la cobertura por año es desigual (28 a 82 registros).
14. **¿Cómo prueban que funciona?** Con 48 pruebas automáticas en pytest sobre las reglas de inventario, la limpieza del Excel, el diccionario de datos, la tabla depurada, la conversión a pares, el pronóstico y la brecha de precio (`python -m pytest`).
15. **¿Los datos del pronóstico y del prototipo son reales?** No. Son simulados y están marcados como [Simulado] en pantalla, porque el sistema solo tiene 30 días de ventas. Sirven para mostrar el método; con datos reales de 24 meses funcionaría igual.
16. **¿Qué es el MAPE?** El error porcentual promedio del pronóstico. Se calcula con un backtest, es decir, pronosticando meses que ya se conocen y comparando con lo real. Con datos simulados demuestra el método, no la realidad (ver la pregunta 19).
17. **¿Se puede usar otra base de datos?** Sí. Por defecto es SQLite, pero si se define la variable de entorno `DATABASE_URL` con una dirección `postgresql+psycopg://…`, el sistema usa PostgreSQL sin cambiar el código.
18. **¿Qué le falta al sistema?** Editar o anular ventas, conexión con el punto de venta, un modelo de IA entrenado con fotos de Manaco, una base PostgreSQL en un servidor con HTTPS para muchos usuarios, y datos de Bolivia (INE o Aduana).
19. **¿El MAPE prueba que el contrabando reduce la demanda?** No. El historial simulado se generó con ese efecto, así que el ajuste lo recupera casi por construcción. El backtest demuestra que el método funciona; la magnitud real se valida con ventas reales de Manaco.
20. **¿Cambian las conclusiones si se mide valor o cantidad?** Por categoría, no: el orden es el mismo y Deportivo importa 2,97 veces lo que exporta en valor y 2,91 en pares. Por socio, sí: República Checa entra al top 6 de proveedores por pares y no por valor, porque su calzado es el más barato de la base (unos 9 USD por par).
21. **¿Por qué la brecha de precio es la misma en las tres líneas?** Porque compara calzado equivalente: la referencia del mercado informal es un solo precio promedio, así que se usa como descuento informal (≈12%) y se aplica al precio de cada línea. Comparar el Cuero, el más caro, contra un precio informal promedio inflaría su brecha de forma artificial. Con precios informales por línea, la brecha sería distinta en cada una.

---

## 9. Usuarios de prueba y cómo abrir el sistema

| Usuario | Contraseña | Rol | Lo crea |
| --- | --- | --- | --- |
| `admin` | `manaco2026` | administrador | `scripts/init_db.py` |
| `encargado` | `manaco2026` | encargado | `scripts/seed_demo.py` |
| `gerencia` | `manaco2026` | gerencia | `scripts/seed_demo.py` |

**Abrir el sistema** (en PowerShell o Anaconda Prompt, dentro de la carpeta del proyecto y con el entorno activado: `.venv` o `conda activate manaco`):

```
python scripts\init_db.py      # la primera vez, y cada vez que cambie la limpieza del Excel: tablas, Excel y usuario admin
python scripts\seed_demo.py    # datos de demo (borra tiendas, productos, aperturas, ventas y cierres anteriores)
python scripts\seed_solucion.py  # datos [Simulado] del prototipo de escenario (correrlo después de seed_demo)
streamlit run app.py
```

- Se abre en `http://localhost:8501`.
- Para tomar la foto con el celular: conecte el celular a la misma red Wi-Fi y abra la *Network URL* que muestra Streamlit.
- Para cerrar el sistema, presione `Ctrl + C` en la ventana de PowerShell.
- Si cambia el código, cierre el sistema con `Ctrl + C` y vuelva a ejecutar `streamlit run app.py`.
- Pruebas automáticas: `python -m pytest` (48 pruebas).
- Después de cada `git pull`, ejecute `pip install -r requirements.txt` (instala librerías nuevas, como `psycopg` y `python-docx`) y `python scripts\init_db.py` (recarga el Excel con la limpieza vigente).

⚠️ Estas contraseñas son de prueba. En un uso real deben cambiarse desde la página **Usuarios**.
