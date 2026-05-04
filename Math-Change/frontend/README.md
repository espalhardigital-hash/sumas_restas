# Math Challenge

Juego educativo de aritmética con dificultad progresiva y sistema de puntuación.

## Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI (Python 3.10) + SQLAlchemy async
- **Base de Datos**: PostgreSQL 15
- **Storage**: MinIO (S3-compatible) para avatares
- **Auth**: JWT (bcrypt + python-jose)

## Run Locally (Docker)

```bash
# Iniciar todos los servicios (PostgreSQL + MinIO + Backend + Frontend)
docker compose up -d --build

# Crear las tablas en la base de datos
docker compose exec backend python setup_db.py

# (Opcional) Cargar datos de prueba
docker compose exec backend python seed_data.py
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin123)
