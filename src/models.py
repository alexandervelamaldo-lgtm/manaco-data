"""Modelos SQLAlchemy 2.x del sistema Manaco Data."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


class Usuario(Base):
    """Persona que usa el sistema, con su rol."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hash_contrasena: Mapped[str] = mapped_column(String(100))
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Tienda(Base):
    """Tienda o almacén de Manaco."""

    __tablename__ = "tiendas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    ciudad: Mapped[str] = mapped_column(String(40))
    tipo: Mapped[str] = mapped_column(String(20), default="tienda")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    """Modelo de calzado (un código por talla y color)."""

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_modelo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    categoria: Mapped[str] = mapped_column(String(30))
    codigo_sa6: Mapped[int] = mapped_column(Integer)
    talla: Mapped[str] = mapped_column(String(10))
    color: Mapped[str] = mapped_column(String(30))
    precio_venta_bs: Mapped[float] = mapped_column(Float)
    costo_bs: Mapped[float] = mapped_column(Float)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Apertura(Base):
    """Saldo inicial de un producto en una tienda al empezar el día."""

    __tablename__ = "aperturas"
    __table_args__ = (UniqueConstraint("fecha", "tienda_id", "producto_id", name="uq_apertura_dia"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    saldo_inicial: Mapped[int] = mapped_column(Integer)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    tienda: Mapped[Tienda] = relationship()
    producto: Mapped[Producto] = relationship()


class Venta(Base):
    """Venta de uno o más pares de un producto."""

    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    hora: Mapped[time] = mapped_column(Time)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario_bs: Mapped[float] = mapped_column(Float)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    tienda: Mapped[Tienda] = relationship()
    producto: Mapped[Producto] = relationship()


class Cierre(Base):
    """Conteo de cierre y conciliación contra el saldo esperado."""

    __tablename__ = "cierres"
    __table_args__ = (UniqueConstraint("fecha", "tienda_id", "producto_id", name="uq_cierre_dia"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tiendas.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    saldo_inicial: Mapped[int] = mapped_column(Integer)
    total_vendido: Mapped[int] = mapped_column(Integer)
    saldo_esperado: Mapped[int] = mapped_column(Integer)
    conteo_ia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conteo_final: Mapped[int] = mapped_column(Integer)
    diferencia: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    foto_ruta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confianza_ia: Mapped[float | None] = mapped_column(Float, nullable=True)
    observacion: Mapped[str] = mapped_column(Text, default="")
    alerta_atendida: Mapped[bool] = mapped_column(Boolean, default=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    tienda: Mapped[Tienda] = relationship()
    producto: Mapped[Producto] = relationship()


class AnulacionCierre(Base):
    """Registro de auditoría de un cierre anulado por el administrador."""

    __tablename__ = "anulaciones_cierre"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date)
    tienda_id: Mapped[int] = mapped_column(Integer)
    producto_id: Mapped[int] = mapped_column(Integer)
    conteo_final: Mapped[int] = mapped_column(Integer)
    diferencia: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    motivo: Mapped[str] = mapped_column(Text)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    anulado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ComercioExterior(Base):
    """Registro de comercio exterior de calzado (Excel limpio)."""

    __tablename__ = "comercio_exterior"

    id: Mapped[int] = mapped_column(primary_key=True)
    pais_reportante: Mapped[str] = mapped_column(String(60))
    flujo_comercial: Mapped[str] = mapped_column(String(20))
    anio: Mapped[int] = mapped_column(Integer)
    codigo_sa6: Mapped[int] = mapped_column(Integer)
    categoria_calzado: Mapped[str] = mapped_column(String(150))
    socio_comercial: Mapped[str] = mapped_column(String(80))
    valor_miles_usd: Mapped[float] = mapped_column(Float)
    cantidad_pares: Mapped[int] = mapped_column(Integer)
    valor_usd: Mapped[float] = mapped_column(Float)
    valor_usd_por_par: Mapped[float] = mapped_column(Float)
    registro_valido: Mapped[bool] = mapped_column(Boolean, default=True)


class BitacoraLimpieza(Base):
    """Cada regla de limpieza aplicada al Excel y su efecto."""

    __tablename__ = "bitacora_limpieza"

    id: Mapped[int] = mapped_column(primary_key=True)
    regla: Mapped[str] = mapped_column(String(120))
    filas_afectadas: Mapped[int] = mapped_column(Integer)
    detalle: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# --- Esquema en estrella (Manaco_Caso_Solucion_y_Prototipo.md, sección 2) ----
# ``Producto`` ya cumple el rol de dim_producto, ``Tienda`` el de dim_tienda,
# ``Venta`` el de fact_ventas, ``Apertura``/``Cierre`` el de fact_inventario y
# ``ComercioExterior`` el de ref_comercio_exterior: no se duplican aquí.
# Las siguientes tablas completan las dimensiones y hechos que faltaban.


class DimFecha(Base):
    """Dimensión de calendario: una fila por día, con rasgos de estacionalidad."""

    __tablename__ = "dim_fecha"

    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    inicio_clases: Mapped[bool] = mapped_column(Boolean, default=False)
    feriado: Mapped[bool] = mapped_column(Boolean, default=False)


class FactProduccion(Base):
    """Lote de producción: pares fabricados y sus costos."""

    __tablename__ = "fact_produccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    lote: Mapped[str] = mapped_column(String(30))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    pares: Mapped[int] = mapped_column(Integer)
    costo_insumos_bs: Mapped[float] = mapped_column(Float)
    costo_mano_obra_bs: Mapped[float] = mapped_column(Float)

    producto: Mapped[Producto] = relationship()


class FactCalidad(Base):
    """Defectos y devoluciones observados en un lote de producción."""

    __tablename__ = "fact_calidad"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    lote: Mapped[str] = mapped_column(String(30))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    defectos: Mapped[int] = mapped_column(Integer, default=0)
    devoluciones: Mapped[int] = mapped_column(Integer, default=0)
    motivo: Mapped[str] = mapped_column(String(120), default="")

    producto: Mapped[Producto] = relationship()


class RefMercadoLocal(Base):
    """Referencia de precios de la competencia y tipo de cambio paralelo."""

    __tablename__ = "ref_mercado_local"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    ciudad: Mapped[str] = mapped_column(String(40))
    mercado: Mapped[str] = mapped_column(String(80))
    precio_competidor_bs: Mapped[float] = mapped_column(Float)
    tipo_cambio_paralelo: Mapped[float] = mapped_column(Float)


class LogIngesta(Base):
    """Registro de cada carga de datos recibida de una sucursal."""

    __tablename__ = "log_ingesta"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    sucursal: Mapped[str] = mapped_column(String(80))
    archivo: Mapped[str] = mapped_column(String(120))
    filas_leidas: Mapped[int] = mapped_column(Integer)
    filas_corregidas: Mapped[int] = mapped_column(Integer)
    filas_rechazadas: Mapped[int] = mapped_column(Integer)
