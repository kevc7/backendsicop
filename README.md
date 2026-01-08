# ECO-MOVE Backend API

API REST para el sistema de gestión de alquileres de vehículos eléctricos ECO-MOVE S.A.

## Stack
- FastAPI 0.109.0
- SQLAlchemy 2.0
- PostgreSQL (Supabase)
- JWT Authentication

## Endpoints

### Autenticación
- `POST /auth/login` - Iniciar sesión
- `POST /auth/register` - Registrar usuario
- `GET /auth/me` - Obtener perfil

### Clientes
- `GET /clientes/` - Listar clientes
- `POST /clientes/` - Crear cliente
- `GET /clientes/{id}` - Obtener cliente
- `PUT /clientes/{id}` - Actualizar cliente
- `DELETE /clientes/{id}` - Eliminar cliente

### Vehículos
- `GET /vehiculos/` - Listar vehículos
- `GET /vehiculos/disponibles` - Vehículos disponibles
- `GET /vehiculos/{id}` - Obtener vehículo

### Alquileres
- `GET /alquileres/` - Listar alquileres
- `POST /alquileres/` - Crear alquiler
- `POST /alquileres/calcular` - Calcular costos
- `PATCH /alquileres/{id}/cancelar` - Cancelar alquiler

### Devoluciones
- `GET /devoluciones/` - Listar devoluciones
- `POST /devoluciones/` - Registrar devolución
- `POST /devoluciones/calcular` - Calcular penalizaciones

### Reportes
- `GET /reportes/total-recaudado`
- `GET /reportes/vehiculos-mas-alquilados`
- `GET /reportes/clientes-multiples-alquileres`
- `GET /reportes/alquileres-doble-descuento`
- `GET /reportes/clientes-multa-mayor-deposito`

## Deploy

### Variables de Entorno Requeridas
```
DATABASE_URL=postgresql://...
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### Local
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Render
1. Conectar repositorio
2. Configurar variables de entorno
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
