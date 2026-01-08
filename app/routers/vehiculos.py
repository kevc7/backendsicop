"""
ECO-MOVE API - Vehículos Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Vehiculo, Usuario
from app.schemas import VehiculoCreate, VehiculoUpdate, VehiculoResponse, EstadoVehiculoEnum
from app.auth import get_current_user, get_staff_user, get_admin_user

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])


@router.get("/", response_model=List[VehiculoResponse])
def get_vehiculos(
    skip: int = 0,
    limit: int = 100,
    estado: EstadoVehiculoEnum = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los vehículos"""
    query = db.query(Vehiculo)
    
    if estado:
        query = query.filter(Vehiculo.estado == estado.value)
    
    vehiculos = query.offset(skip).limit(limit).all()
    return vehiculos


@router.get("/disponibles", response_model=List[VehiculoResponse])
def get_vehiculos_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista vehículos disponibles para alquilar"""
    vehiculos = db.query(Vehiculo).filter(Vehiculo.estado == "disponible").all()
    return vehiculos


@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
def get_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un vehículo por ID"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehiculo


@router.get("/codigo/{codigo}", response_model=VehiculoResponse)
def get_vehiculo_by_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca un vehículo por código"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.codigo == codigo.upper()).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehiculo


@router.post("/", response_model=VehiculoResponse, status_code=status.HTTP_201_CREATED)
def create_vehiculo(
    vehiculo: VehiculoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_admin_user)
):
    """Crea un nuevo vehículo (solo admin)"""
    # Verificar código único
    existing = db.query(Vehiculo).filter(Vehiculo.codigo == vehiculo.codigo.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un vehículo con ese código"
        )
    
    db_vehiculo = Vehiculo(**vehiculo.model_dump())
    db_vehiculo.codigo = db_vehiculo.codigo.upper()
    db.add(db_vehiculo)
    db.commit()
    db.refresh(db_vehiculo)
    return db_vehiculo


@router.put("/{vehiculo_id}", response_model=VehiculoResponse)
def update_vehiculo(
    vehiculo_id: int,
    vehiculo_update: VehiculoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_admin_user)
):
    """Actualiza un vehículo (solo admin)"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    update_data = vehiculo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "estado":
            setattr(vehiculo, field, value.value if value else None)
        else:
            setattr(vehiculo, field, value)
    
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


@router.patch("/{vehiculo_id}/estado")
def update_vehiculo_estado(
    vehiculo_id: int,
    estado: EstadoVehiculoEnum,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Actualiza el estado de un vehículo"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    vehiculo.estado = estado.value
    db.commit()
    
    return {"message": f"Estado actualizado a '{estado.value}'"}


@router.delete("/{vehiculo_id}")
def delete_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_admin_user)
):
    """Elimina un vehículo (solo admin)"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Verificar que no tenga alquileres activos
    if vehiculo.alquileres:
        alquileres_activos = [a for a in vehiculo.alquileres if a.estado == "activo"]
        if alquileres_activos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un vehículo con alquileres activos"
            )
    
    db.delete(vehiculo)
    db.commit()
    return {"message": "Vehículo eliminado exitosamente"}
