"""
ECO-MOVE API - Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# =====================================================
# ENUMS
# =====================================================
class RolEnum(str, Enum):
    admin = "admin"
    empleado = "empleado"
    cliente = "cliente"


class EstadoVehiculoEnum(str, Enum):
    disponible = "disponible"
    alquilado = "alquilado"
    mantenimiento = "mantenimiento"


class EstadoAlquilerEnum(str, Enum):
    activo = "activo"
    devuelto = "devuelto"
    cancelado = "cancelado"


# =====================================================
# USUARIO SCHEMAS
# =====================================================
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    rol: RolEnum = RolEnum.cliente


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    rol: Optional[RolEnum] = None
    activo: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


# =====================================================
# CLIENTE SCHEMAS
# =====================================================
class ClienteBase(BaseModel):
    dni: str = Field(..., min_length=6, max_length=20)
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    fecha_nacimiento: date
    es_frecuente: bool = False
    direccion: Optional[str] = None


class ClienteCreate(ClienteBase):
    usuario_id: Optional[int] = None


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    es_frecuente: Optional[bool] = None
    direccion: Optional[str] = None


class ClienteResponse(ClienteBase):
    id: int
    usuario_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================================================
# VEHICULO SCHEMAS
# =====================================================
class VehiculoBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=10)
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    tarifa_diaria: Decimal = Field(..., gt=0)
    requiere_mayor_edad: bool = False
    imagen_url: Optional[str] = None


class VehiculoCreate(VehiculoBase):
    pass


class VehiculoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    tarifa_diaria: Optional[Decimal] = Field(None, gt=0)
    requiere_mayor_edad: Optional[bool] = None
    estado: Optional[EstadoVehiculoEnum] = None
    imagen_url: Optional[str] = None


class VehiculoResponse(VehiculoBase):
    id: int
    estado: EstadoVehiculoEnum
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================================================
# ALQUILER SCHEMAS
# =====================================================
class AlquilerBase(BaseModel):
    cliente_id: int
    vehiculo_id: int
    fecha_inicio: date
    fecha_tentativa_devolucion: date
    notas: Optional[str] = None


class AlquilerCreate(AlquilerBase):
    pass


class AlquilerCalculado(BaseModel):
    """Respuesta con cálculos del alquiler"""
    dias: int
    importe: Decimal
    descuento_uso_extendido: Decimal
    descuento_cliente_frecuente: Decimal
    deposito: Decimal
    total_pagar: Decimal


class AlquilerResponse(BaseModel):
    id: int
    cliente_id: int
    vehiculo_id: int
    fecha_inicio: date
    fecha_tentativa_devolucion: date
    dias: int
    importe: Decimal
    descuento_uso_extendido: Decimal
    descuento_cliente_frecuente: Decimal
    deposito: Decimal
    total_pagar: Decimal
    estado: EstadoAlquilerEnum
    notas: Optional[str]
    created_at: datetime
    
    # Relaciones anidadas
    cliente: Optional[ClienteResponse] = None
    vehiculo: Optional[VehiculoResponse] = None
    
    class Config:
        from_attributes = True


# =====================================================
# DEVOLUCION SCHEMAS
# =====================================================
class DevolucionBase(BaseModel):
    alquiler_id: int
    fecha_devolucion_real: date
    observaciones: Optional[str] = None


class DevolucionCreate(DevolucionBase):
    pass


class DevolucionCalculada(BaseModel):
    """Respuesta con cálculos de la devolución"""
    dias_mora: int
    multa: Decimal
    deposito_devuelto: Decimal
    monto_adicional: Decimal
    total_final: Decimal


class DevolucionResponse(BaseModel):
    id: int
    alquiler_id: int
    fecha_devolucion_real: date
    dias_mora: int
    multa: Decimal
    deposito_devuelto: Decimal
    monto_adicional: Decimal
    total_final: Decimal
    observaciones: Optional[str]
    created_at: datetime
    
    # Relación anidada
    alquiler: Optional[AlquilerResponse] = None
    
    class Config:
        from_attributes = True


# =====================================================
# REPORTES SCHEMAS
# =====================================================
class ClienteMultiplesAlquileresResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    total_alquileres: int


class VehiculoMasAlquiladoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    total_alquileres: int
    ingresos_generados: Optional[Decimal]


class TotalRecaudadoResponse(BaseModel):
    total_alquileres: Optional[Decimal]
    total_depositos: Optional[Decimal]
    total_multas: Optional[Decimal]
    total_recaudado: Optional[Decimal]
