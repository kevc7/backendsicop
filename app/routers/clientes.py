"""
ECO-MOVE API - Clientes Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cliente, Usuario
from app.schemas import ClienteCreate, ClienteUpdate, ClienteResponse
from app.auth import get_current_user, get_staff_user

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/", response_model=List[ClienteResponse])
def get_clientes(
    skip: int = 0,
    limit: int = 100,
    es_frecuente: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Lista todos los clientes (admin/empleado)"""
    query = db.query(Cliente)
    
    if es_frecuente is not None:
        query = query.filter(Cliente.es_frecuente == es_frecuente)
    
    clientes = query.offset(skip).limit(limit).all()
    return clientes


@router.get("/{cliente_id}", response_model=ClienteResponse)
def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Obtiene un cliente por ID"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/dni/{dni}", response_model=ClienteResponse)
def get_cliente_by_dni(
    dni: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Busca un cliente por DNI"""
    cliente = db.query(Cliente).filter(Cliente.dni == dni).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Crea un nuevo cliente"""
    # Verificar DNI único
    existing = db.query(Cliente).filter(Cliente.dni == cliente.dni).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con ese DNI"
        )
    
    db_cliente = Cliente(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(
    cliente_id: int,
    cliente_update: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Actualiza un cliente"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = cliente_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cliente, field, value)
    
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}")
def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_staff_user)
):
    """Elimina un cliente"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar que no tenga alquileres activos
    if cliente.alquileres:
        alquileres_activos = [a for a in cliente.alquileres if a.estado == "activo"]
        if alquileres_activos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un cliente con alquileres activos"
            )
    
    db.delete(cliente)
    db.commit()
    return {"message": "Cliente eliminado exitosamente"}
