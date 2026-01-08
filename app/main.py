"""
ECO-MOVE API - Main Application
Sistema de gestión de alquiler de vehículos eléctricos
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import auth, usuarios, clientes, vehiculos, alquileres, devoluciones, reportes

settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    ## 🚲 ECO-MOVE API
    
    Sistema de gestión de alquiler de vehículos eléctricos personales.
    
    ### Funcionalidades:
    - **Autenticación**: Login/registro con JWT y roles (admin, empleado, cliente)
    - **Clientes**: CRUD completo de clientes
    - **Vehículos**: Gestión del catálogo de vehículos eléctricos
    - **Alquileres**: Registro de alquileres con cálculos automáticos de descuentos
    - **Devoluciones**: Registro de devoluciones con cálculo de multas
    - **Reportes**: Consultas y estadísticas del negocio
    
    ### Reglas de negocio:
    - Descuento 15% por uso extendido (> 5 días)
    - Descuento 10% adicional para clientes frecuentes
    - Depósito del 12% del importe
    - Multa del 10% del importe diario por día de retraso
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(vehiculos.router)
app.include_router(alquileres.router)
app.include_router(devoluciones.router)
app.include_router(reportes.router)


@app.get("/", tags=["Health"])
def root():
    """Endpoint de salud"""
    return {
        "message": "🚲 ECO-MOVE API está funcionando",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check para monitoreo"""
    return {"status": "healthy"}
