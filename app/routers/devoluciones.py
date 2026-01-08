"""
ECO-MOVE API - Devoluciones Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Devolucion, Alquiler, Vehiculo, Usuario
from app.schemas import DevolucionCreate, DevolucionResponse, DevolucionCalculada
from app.auth import get_staff_user
from app.services import calcular_devolucion

router = APIRouter(prefix="/devoluciones", tags=["Devoluciones"])


@router.get("/", response_model=List[DevolucionResponse])
def get_devoluciones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Lista todas las devoluciones"""
    devoluciones = db.query(Devolucion).options(
        joinedload(Devolucion.alquiler).joinedload(Alquiler.cliente),
        joinedload(Devolucion.alquiler).joinedload(Alquiler.vehiculo)
    ).order_by(Devolucion.created_at.desc()).offset(skip).limit(limit).all()
    return devoluciones


@router.get("/{devolucion_id}", response_model=DevolucionResponse)
def get_devolucion(
    devolucion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Obtiene una devolución por ID"""
    devolucion = db.query(Devolucion).options(
        joinedload(Devolucion.alquiler).joinedload(Alquiler.cliente),
        joinedload(Devolucion.alquiler).joinedload(Alquiler.vehiculo)
    ).filter(Devolucion.id == devolucion_id).first()
    
    if not devolucion:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return devolucion


@router.post("/calcular", response_model=DevolucionCalculada)
def calcular_preview(
    devolucion_data: DevolucionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Calcula los valores de devolución sin crear el registro (preview)"""
    # Obtener alquiler
    alquiler = db.query(Alquiler).filter(Alquiler.id == devolucion_data.alquiler_id).first()
    if not alquiler:
        raise HTTPException(status_code=404, detail="Alquiler no encontrado")
    
    if alquiler.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El alquiler no está activo"
        )
    
    # Calcular
    resultado = calcular_devolucion(
        alquiler=alquiler,
        fecha_devolucion_real=devolucion_data.fecha_devolucion_real
    )
    
    return DevolucionCalculada(**resultado)


@router.post("/", response_model=DevolucionResponse, status_code=status.HTTP_201_CREATED)
def create_devolucion(
    devolucion_data: DevolucionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Registra la devolución de un vehículo"""
    # Obtener alquiler
    alquiler = db.query(Alquiler).filter(Alquiler.id == devolucion_data.alquiler_id).first()
    if not alquiler:
        raise HTTPException(status_code=404, detail="Alquiler no encontrado")
    
    if alquiler.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El alquiler no está activo"
        )
    
    # Verificar que no exista ya una devolución
    existing = db.query(Devolucion).filter(Devolucion.alquiler_id == alquiler.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una devolución para este alquiler"
        )
    
    # Calcular valores
    calculos = calcular_devolucion(
        alquiler=alquiler,
        fecha_devolucion_real=devolucion_data.fecha_devolucion_real
    )
    
    # Crear devolución
    db_devolucion = Devolucion(
        alquiler_id=devolucion_data.alquiler_id,
        fecha_devolucion_real=devolucion_data.fecha_devolucion_real,
        observaciones=devolucion_data.observaciones,
        **calculos
    )
    
    # Actualizar estado del alquiler
    alquiler.estado = "devuelto"
    
    # Liberar vehículo
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == alquiler.vehiculo_id).first()
    if vehiculo:
        vehiculo.estado = "disponible"
    
    db.add(db_devolucion)
    db.commit()
    db.refresh(db_devolucion)
    
    # Cargar relaciones
    db_devolucion = db.query(Devolucion).options(
        joinedload(Devolucion.alquiler).joinedload(Alquiler.cliente),
        joinedload(Devolucion.alquiler).joinedload(Alquiler.vehiculo)
    ).filter(Devolucion.id == db_devolucion.id).first()
    
    return db_devolucion
