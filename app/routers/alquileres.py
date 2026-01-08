"""
ECO-MOVE API - Alquileres Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Alquiler, Cliente, Vehiculo, Usuario
from app.schemas import AlquilerCreate, AlquilerResponse, AlquilerCalculado
from app.auth import get_current_user, get_staff_user
from app.services import calcular_alquiler, validar_edad_cliente

router = APIRouter(prefix="/alquileres", tags=["Alquileres"])


@router.get("/", response_model=List[AlquilerResponse])
def get_alquileres(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    cliente_id: int = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Lista todos los alquileres"""
    query = db.query(Alquiler).options(
        joinedload(Alquiler.cliente),
        joinedload(Alquiler.vehiculo)
    )
    
    if estado:
        query = query.filter(Alquiler.estado == estado)
    if cliente_id:
        query = query.filter(Alquiler.cliente_id == cliente_id)
    
    alquileres = query.order_by(Alquiler.created_at.desc()).offset(skip).limit(limit).all()
    return alquileres


@router.get("/activos", response_model=List[AlquilerResponse])
def get_alquileres_activos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Lista alquileres activos"""
    alquileres = db.query(Alquiler).options(
        joinedload(Alquiler.cliente),
        joinedload(Alquiler.vehiculo)
    ).filter(Alquiler.estado == "activo").all()
    return alquileres


@router.get("/{alquiler_id}", response_model=AlquilerResponse)
def get_alquiler(
    alquiler_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Obtiene un alquiler por ID"""
    alquiler = db.query(Alquiler).options(
        joinedload(Alquiler.cliente),
        joinedload(Alquiler.vehiculo)
    ).filter(Alquiler.id == alquiler_id).first()
    
    if not alquiler:
        raise HTTPException(status_code=404, detail="Alquiler no encontrado")
    return alquiler


@router.post("/calcular", response_model=AlquilerCalculado)
def calcular_preview(
    alquiler_data: AlquilerCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Calcula el costo del alquiler sin crear el registro (preview)"""
    # Obtener cliente y vehículo
    cliente = db.query(Cliente).filter(Cliente.id == alquiler_data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == alquiler_data.vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Validar fecha
    if alquiler_data.fecha_tentativa_devolucion < alquiler_data.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de devolución debe ser posterior a la fecha de inicio"
        )
    
    # Calcular
    resultado = calcular_alquiler(
        vehiculo=vehiculo,
        cliente=cliente,
        fecha_inicio=alquiler_data.fecha_inicio,
        fecha_tentativa_devolucion=alquiler_data.fecha_tentativa_devolucion
    )
    
    return AlquilerCalculado(**resultado)


@router.post("/", response_model=AlquilerResponse, status_code=status.HTTP_201_CREATED)
def create_alquiler(
    alquiler_data: AlquilerCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Crea un nuevo alquiler"""
    # Obtener cliente
    cliente = db.query(Cliente).filter(Cliente.id == alquiler_data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Obtener vehículo
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == alquiler_data.vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Verificar disponibilidad
    if vehiculo.estado != "disponible":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El vehículo no está disponible (estado: {vehiculo.estado})"
        )
    
    # Validar edad del cliente
    es_valido, mensaje = validar_edad_cliente(cliente, vehiculo)
    if not es_valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )
    
    # Validar fechas
    if alquiler_data.fecha_tentativa_devolucion < alquiler_data.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de devolución debe ser posterior a la fecha de inicio"
        )
    
    # Calcular valores
    calculos = calcular_alquiler(
        vehiculo=vehiculo,
        cliente=cliente,
        fecha_inicio=alquiler_data.fecha_inicio,
        fecha_tentativa_devolucion=alquiler_data.fecha_tentativa_devolucion
    )
    
    # Crear alquiler
    db_alquiler = Alquiler(
        cliente_id=alquiler_data.cliente_id,
        vehiculo_id=alquiler_data.vehiculo_id,
        fecha_inicio=alquiler_data.fecha_inicio,
        fecha_tentativa_devolucion=alquiler_data.fecha_tentativa_devolucion,
        notas=alquiler_data.notas,
        **calculos
    )
    
    # Actualizar estado del vehículo
    vehiculo.estado = "alquilado"
    
    db.add(db_alquiler)
    db.commit()
    db.refresh(db_alquiler)
    
    # Cargar relaciones
    db_alquiler = db.query(Alquiler).options(
        joinedload(Alquiler.cliente),
        joinedload(Alquiler.vehiculo)
    ).filter(Alquiler.id == db_alquiler.id).first()
    
    return db_alquiler


@router.patch("/{alquiler_id}/cancelar")
def cancelar_alquiler(
    alquiler_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Cancela un alquiler activo"""
    alquiler = db.query(Alquiler).filter(Alquiler.id == alquiler_id).first()
    if not alquiler:
        raise HTTPException(status_code=404, detail="Alquiler no encontrado")
    
    if alquiler.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden cancelar alquileres activos"
        )
    
    # Liberar vehículo
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == alquiler.vehiculo_id).first()
    if vehiculo:
        vehiculo.estado = "disponible"
    
    alquiler.estado = "cancelado"
    db.commit()
    
    return {"message": "Alquiler cancelado exitosamente"}
