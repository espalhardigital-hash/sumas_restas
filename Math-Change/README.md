# Math Challenge (Sumas y Restas)

Aplicación educativa para practicar aritmética con niveles progresivos, sistema de usuarios y estadísticas detalladas.

## 🚀 Infraestructura Local

Esta versión de la aplicación ha sido migrada para funcionar de forma **100% autónoma** en servidores privados (VM), eliminando dependencias de servicios externos como Firebase o Supabase.

### Stack Tecnológico:
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python) + SQLAlchemy Async
- **Base de Datos**: PostgreSQL 15
- **Almacenamiento**: MinIO (S3-Compatible) para avatares
- **Autenticación**: JWT (JSON Web Tokens) nativo

## 🛠️ Instalación y Despliegue

Para desplegar la aplicación en tu propia infraestructura o máquina virtual, consulta la guía detallada:

👉 **[Guía de Despliegue (DEPLOY.md)](./DEPLOY.md)**

### Inicio Rápido (Docker):

1. Configura tu entorno:
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales de PostgreSQL y MinIO
   ```

2. Levanta los contenedores:
   ```bash
   docker compose up -d --build
   ```

3. Inicializa la base de datos:
   ```bash
   docker compose exec backend python setup_db.py
   ```

## 🧪 Testing

La suite de pruebas permite validar la conexión con la base de datos y el almacenamiento local:

```bash
docker compose exec backend python tests/test_db_connection.py
docker compose exec backend python tests/test_crud_flow.py
```
