# 🐘 Setup de PostgreSQL y Migraciones para Math-Change

Este documento contiene las instrucciones para instalar PostgreSQL por separado en una máquina virtual (Ubuntu/Debian) y el script SQL para crear la estructura de la base de datos (tablas, índices y relaciones) necesaria para la aplicación Math-Change.

---

## 1. Instalación de PostgreSQL en la Máquina Virtual

Si usas Ubuntu/Debian, ejecuta los siguientes comandos en la terminal de la VM:

```bash
# 1. Actualizar los repositorios
sudo apt update

# 2. Instalar PostgreSQL y utilidades adicionales
sudo apt install postgresql postgresql-contrib -y

# 3. Verificar que el servicio está corriendo
sudo systemctl status postgresql
```

---

## 2. Creación de Usuario y Base de Datos

Entra a la consola de PostgreSQL usando el usuario por defecto `postgres`:

```bash
sudo -u postgres psql
```

Dentro de la consola de `psql`, ejecuta los siguientes comandos para crear la base de datos y el usuario (puedes cambiar las contraseñas según tu entorno):

```sql
-- Crear la base de datos
CREATE DATABASE app;

-- Crear un usuario específico para la aplicación
CREATE USER math_user WITH ENCRYPTED PASSWORD 'tu_password_seguro';

-- Otorgar privilegios sobre la base de datos al nuevo usuario
GRANT ALL PRIVILEGES ON DATABASE app TO math_user;

-- Conectarse a la nueva base de datos para darle permisos en el esquema public
\c app
GRANT ALL ON SCHEMA public TO math_user;

-- Salir de la consola
\q
```

---

## 3. Script SQL de Inicialización (Migración Inicial)

Este es el script SQL exacto basado en los modelos de SQLAlchemy (`sql_models.py`) de la aplicación.
Guarda este contenido en un archivo llamado `001_init_schema.sql` en tu VM.

```sql
-- ========================================================
-- MIGRACIÓN INICIAL: MATH-CHANGE
-- Motor: PostgreSQL
-- ========================================================

-- Conectarse a la base de datos (Si ejecutas el script directamente via psql)
-- \c app;

-- Habilitar extensión para generar UUIDs si en el futuro se requieren a nivel de DB
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- TABLA: users
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY, -- El backend genera un UUID (como String)
    username VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR,
    role VARCHAR DEFAULT 'USER',
    status VARCHAR DEFAULT 'ACTIVE',
    avatar VARCHAR,
    settings JSONB DEFAULT '{}'::jsonb,
    unlocked_level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Crear índice para búsquedas por email
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- ==========================================
-- TABLA: scores
-- ==========================================
CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    score INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    avg_time DOUBLE PRECISION NOT NULL,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR,
    difficulty VARCHAR,
    
    -- Relación con la tabla users
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES users(id)
        ON DELETE CASCADE -- Si se borra el usuario, se borran sus scores
);

-- Crear índice para acelerar consultas por usuario (muy común en los dashboards)
CREATE INDEX IF NOT EXISTS ix_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS ix_scores_id ON scores(id);

-- ==========================================
-- FIN DEL SCRIPT
-- ==========================================
```

### ¿Cómo ejecutar este script?

Una vez guardado el archivo `001_init_schema.sql`, impórtalo a tu base de datos mediante el siguiente comando en la terminal:

```bash
# Cambia 'app' y 'math_user' si usaste otros nombres en el paso 2
psql -U math_user -d app -f 001_init_schema.sql
```
*(Te pedirá la contraseña del usuario `math_user`)*

---

## 4. Alternativa: Inicialización con el Backend de Python

Dado que el proyecto utiliza **SQLAlchemy**, no necesitas ejecutar SQL manualmente si ya tienes el backend corriendo. Puedes usar el script interno del proyecto para que cree las tablas de forma automatizada.

Si vas a probar esta alternativa, asumiendo que configuraste tu variable de entorno `DATABASE_URL` en el archivo `.env` del backend (apuntando a tu nueva BD instalada, por ejemplo: `postgresql+asyncpg://math_user:tu_password_seguro@localhost:5432/app`):

```bash
# Ejecutar desde la carpeta raíz del backend
python -m app.init_db
```
Este comando, provisto en el código, se conecta y ejecuta `Base.metadata.create_all`, creando exactamente las mismas tablas detalladas en el script SQL de arriba.

---
## 5. Próximos Pasos (Conexión)

Una vez creada la base de datos y ejecutado el script, configura tu archivo `.env` del servidor Backend para apuntar a la IP de la máquina virtual (o a `localhost` si el backend correrá en la misma máquina):

```env
# Ejemplo de configuración para .env
DATABASE_URL=postgresql+asyncpg://math_user:tu_password_seguro@localhost:5432/app
DB_PASSWORD=tu_password_seguro
```
