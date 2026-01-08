"""
ECO-MOVE API - SQLAlchemy Models
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, Text, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    rol = Column(String(20), nullable=False, default="cliente")
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relación con cliente (opcional)
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)
    
    __table_args__ = (
        CheckConstraint("rol IN ('admin', 'empleado', 'cliente')", name="check_rol"),
    )


class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    dni = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20))
    email = Column(String(255))
    fecha_nacimiento = Column(Date, nullable=False)
    es_frecuente = Column(Boolean, default=False)
    direccion = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="cliente")
    alquileres = relationship("Alquiler", back_populates="cliente")


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    tarifa_diaria = Column(Numeric(10, 2), nullable=False)
    requiere_mayor_edad = Column(Boolean, default=False)
    estado = Column(String(20), default="disponible")
    imagen_url = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relaciones
    alquileres = relationship("Alquiler", back_populates="vehiculo")
    
    __table_args__ = (
        CheckConstraint("estado IN ('disponible', 'alquilado', 'mantenimiento')", name="check_estado_vehiculo"),
    )


class Alquiler(Base):
    __tablename__ = "alquileres"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id", ondelete="RESTRICT"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_tentativa_devolucion = Column(Date, nullable=False)
    dias = Column(Integer, nullable=False)
    importe = Column(Numeric(10, 2), nullable=False)
    descuento_uso_extendido = Column(Numeric(10, 2), default=0)
    descuento_cliente_frecuente = Column(Numeric(10, 2), default=0)
    deposito = Column(Numeric(10, 2), nullable=False)
    total_pagar = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), default="activo")
    notas = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="alquileres")
    vehiculo = relationship("Vehiculo", back_populates="alquileres")
    devolucion = relationship("Devolucion", back_populates="alquiler", uselist=False)
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo', 'devuelto', 'cancelado')", name="check_estado_alquiler"),
        CheckConstraint("fecha_tentativa_devolucion >= fecha_inicio", name="check_fechas_alquiler"),
    )


class Devolucion(Base):
    __tablename__ = "devoluciones"
    
    id = Column(Integer, primary_key=True, index=True)
    alquiler_id = Column(Integer, ForeignKey("alquileres.id", ondelete="RESTRICT"), unique=True, nullable=False)
    fecha_devolucion_real = Column(Date, nullable=False)
    dias_mora = Column(Integer, default=0)
    multa = Column(Numeric(10, 2), default=0)
    deposito_devuelto = Column(Numeric(10, 2), default=0)
    monto_adicional = Column(Numeric(10, 2), default=0)
    total_final = Column(Numeric(10, 2), nullable=False)
    observaciones = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.current_timestamp())
    
    # Relaciones
    alquiler = relationship("Alquiler", back_populates="devolucion")
