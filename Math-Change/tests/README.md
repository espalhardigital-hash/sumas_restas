# 🧪 Tests - Math-Change

Esta carpeta contiene todos los tests del proyecto Math-Change.

---

## 📁 Archivos de Test

| Archivo | Descripción |
|---------|-------------|
| `test_s3_connection.py` | Prueba conexión y CRUD con bucket S3/MinIO |
| `test_db_connection.py` | Prueba conexión a PostgreSQL via SQLAlchemy |
| `test_crud_flow.py` | Prueba operaciones CRUD en tablas `users` y `scores` |
| `frontend_test_notes.md` | Notas y metodología de testing |

---

## 🚀 Cómo Ejecutar los Tests

### Prerrequisitos

Los contenedores Docker deben estar corriendo:
```bash
docker compose up -d
```

### Ejecutar Tests

```bash
# Desde la raíz del proyecto (Math-Change/)

# Test de conexión a la base de datos
docker compose exec backend python tests/test_db_connection.py

# Test CRUD completo (users + scores)
docker compose exec backend python tests/test_crud_flow.py

# Test de conexión S3/MinIO
docker compose exec backend python tests/test_s3_connection.py
```

---

## 📋 Descripción Detallada

### 1. `test_db_connection.py` - Database Connection Test

**Finalidad**: Verificar la conexión a PostgreSQL usando SQLAlchemy async.

**Tests incluidos**:
- ✅ Conexión a PostgreSQL via `DATABASE_URL`
- ✅ Ejecución de query `SELECT version()`
- ✅ Listado de tablas existentes

### 2. `test_crud_flow.py` - CRUD Flow Test

**Finalidad**: Probar operaciones CRUD completas contra PostgreSQL.

**Tests incluidos**:
- ✅ **CREATE** - Insertar usuario de prueba con password hash
- ✅ **READ** - Leer usuario por email
- ✅ **UPDATE** - Actualizar `unlocked_level`
- ✅ **DELETE** - Eliminar usuario (cleanup)

### 3. `test_s3_connection.py` - S3/MinIO Bucket Test

**Finalidad**: Verificar la conexión y operaciones con el bucket MinIO.

**Tests incluidos**:
- ✅ Conexión al servidor S3
- ✅ Verificación de bucket
- ✅ **CREATE** - Subir archivo
- ✅ **READ** - Leer archivo
- ✅ **LIST** - Listar objetos
- ✅ **DELETE** - Eliminar archivo

---

## 🔧 Solución de Problemas

### Error: "DATABASE_URL not set"
Verifica que el archivo `.env` existe y tiene `DATABASE_URL` configurado.

### Error: "Connection refused"
1. Verifica que Docker esté corriendo: `docker compose ps`
2. Reconstruye las imágenes: `docker compose build`

### Error: "Bucket not found"
El contenedor `minio-init` debería crear el bucket automáticamente. Si no, accede a http://localhost:9001 y créalo manualmente.
