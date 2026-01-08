"""
ECO-MOVE API - Reportes Router
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Usuario
from app.schemas import (
    ClienteMultiplesAlquileresResponse,
    VehiculoMasAlquiladoResponse,
    TotalRecaudadoResponse
)
from app.auth import get_staff_user

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/clientes-multiples-alquileres", response_model=List[ClienteMultiplesAlquileresResponse])
def get_clientes_multiples_alquileres(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Clientes que alquilaron más de un vehículo"""
    result = db.execute(text("SELECT * FROM v_clientes_multiples_alquileres"))
    rows = result.fetchall()
    
    return [
        ClienteMultiplesAlquileresResponse(
            id=row[0],
            nombre=row[1],
            apellido=row[2],
            dni=row[3],
            total_alquileres=row[4]
        )
        for row in rows
    ]


@router.get("/vehiculos-mas-alquilados", response_model=List[VehiculoMasAlquiladoResponse])
def get_vehiculos_mas_alquilados(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Vehículos más alquilados"""
    result = db.execute(text("SELECT * FROM v_vehiculos_mas_alquilados"))
    rows = result.fetchall()
    
    return [
        VehiculoMasAlquiladoResponse(
            id=row[0],
            codigo=row[1],
            nombre=row[2],
            total_alquileres=row[3],
            ingresos_generados=row[4]
        )
        for row in rows
    ]


@router.get("/alquileres-doble-descuento")
def get_alquileres_doble_descuento(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Alquileres con descuento de cliente frecuente y uso extendido"""
    result = db.execute(text("SELECT * FROM v_alquileres_doble_descuento"))
    rows = result.fetchall()
    
    return [
        {
            "id": row[0],
            "cliente": row[1],
            "vehiculo": row[2],
            "fecha_inicio": row[3],
            "fecha_tentativa_devolucion": row[4],
            "dias": row[5],
            "importe": float(row[6]) if row[6] else 0,
            "descuento_uso_extendido": float(row[7]) if row[7] else 0,
            "descuento_cliente_frecuente": float(row[8]) if row[8] else 0,
            "total_pagar": float(row[9]) if row[9] else 0,
        }
        for row in rows
    ]


@router.get("/total-recaudado", response_model=TotalRecaudadoResponse)
def get_total_recaudado(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Total recaudado por ECO-MOVE (importe neto + depósitos + multas)"""
    result = db.execute(text("SELECT * FROM v_total_recaudado"))
    row = result.fetchone()
    
    if not row:
        return TotalRecaudadoResponse(
            total_alquileres=0,
            total_depositos=0,
            total_multas=0,
            total_recaudado=0
        )
    
    return TotalRecaudadoResponse(
        total_alquileres=row[0],
        total_depositos=row[1],
        total_multas=row[2],
        total_recaudado=row[3]
    )


@router.get("/clientes-multa-mayor-deposito")
def get_clientes_multa_mayor_deposito(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Clientes que devolvieron tarde y pagaron multa mayor al depósito"""
    result = db.execute(text("SELECT * FROM v_clientes_multa_mayor_deposito"))
    rows = result.fetchall()
    
    return [
        {
            "id": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "dni": row[3],
            "alquiler_id": row[4],
            "deposito": float(row[5]) if row[5] else 0,
            "multa": float(row[6]) if row[6] else 0,
            "monto_adicional": float(row[7]) if row[7] else 0,
        }
        for row in rows
    ]
