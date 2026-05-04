# Guía de Despliegue - Math-Change (Sumas y Restas)

## Arquitectura

```
PostgreSQL (base_postgres_general) ← Backend (FastAPI) ← Frontend (Nginx/React)
MinIO (contenedor propio)          ←
```

## Prerrequisitos en la VM
1. **Docker y Docker Compose** instalados.
2. **PostgreSQL** corriendo en contenedor `base_postgres_general` con la base de datos `sumas_restas` creada.
3. **Red Docker** compartida entre los contenedores (ej: `traefik_proxy`).

## Pasos de Despliegue

### 1. Clonar/Subir el proyecto
```bash
git clone https://github.com/espalhardigital-hash/sumas_restas.git
cd sumas_restas/Math-Change
```

### 2. Configurar Variables de Entorno
Editar el archivo `.env`:
```bash
cp .env.example .env
nano .env
```

**Variables Clave:**
- `DATABASE_URL`: Cadena de conexión a PostgreSQL (ej: `postgresql+asyncpg://sumas_user:PASSWORD@base_postgres_general:5432/sumas_restas`)
- `SECRET_KEY`: Clave secreta para JWT (cambiar en producción)
- `S3_*`: Credenciales de tu MinIO
- `VITE_API_URL`: URL pública del backend
- `ALLOWED_ORIGINS`: Dominios permitidos por CORS

### 3. Construir e Iniciar
```bash
docker compose up -d --build
```

### 4. Crear las tablas (primera vez)
```bash
docker compose exec backend python setup_db.py
```

### 5. (Opcional) Cargar datos de prueba
```bash
docker compose exec backend python seed_data.py
```

## Verificación
1. **Frontend**: `http://<IP_VM>:3000` → Pantalla de Login
2. **Backend API**: `http://<IP_VM>:8000/` → Mensaje de bienvenida
3. **Swagger Docs**: `http://<IP_VM>:8000/docs` → Documentación interactiva

## Solución de Problemas

- **Error de Conexión DB**: Verificar que el contenedor `base_postgres_general` está en la misma red Docker que el backend.
- **Error CORS**: Verificar `ALLOWED_ORIGINS` en `.env`.
- **Frontend no conecta al backend**: Verificar `VITE_API_URL` y reconstruir con `--build`.
