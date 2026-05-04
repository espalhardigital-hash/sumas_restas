from fastapi import FastAPI, HTTPException, Body, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import boto3
import io
from PIL import Image, ImageOps

from .schemas import User as UserSchema, UserCreate, UserLogin, ScoreRecord, Token, UserRegister, CategoryLevelUpdate, CategoryProgress
from .db.session import get_db
from .models.sql_models import User, Score
from .auth import (
    get_current_user, 
    get_admin_user, 
    authenticate_user, 
    create_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    verify_password
)

load_dotenv()

# S3 Configuration
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")

app = FastAPI(title="Math-Change API", version="2.0.0")

# Security Headers
if os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true":
    from fastapi import Request
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

# CORS
origins_str = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [origin.strip() for origin in origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def check_connections():
    # S3 warning
    if not all([S3_ACCESS_KEY, S3_SECRET_KEY, S3_ENDPOINT_URL, S3_BUCKET_NAME]):
        print("WARNING: S3 configuration incomplete. Avatar upload will fail.")

@app.get("/")
def read_root():
    return {"message": "Math-Change Backend API v2.0 - PostgreSQL Native"}

# ==================== AUTH ====================

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user and return JWT token."""
    user = await create_user(db, user_data.username, user_data.email, user_data.password)
    
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login with email/password. Returns JWT token."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)

# ==================== USERS ====================

@app.get("/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "avatar": u.avatar,
            "unlocked_level": u.unlocked_level,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]

@app.get("/users/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/users/me/progress", response_model=List[CategoryProgress])
async def get_user_progress(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = select(
        Score.category,
        func.count(Score.id).label('total_games'),
        func.sum(Score.score).label('total_score'),
        func.sum(Score.correct_count).label('total_correct'),
        func.sum(Score.error_count).label('total_errors'),
        func.sum(Score.avg_time).label('total_time_seconds')
    ).where(Score.user_id == current_user["id"]).group_by(Score.category)
    
    result = await db.execute(query)
    rows = result.all()
    
    settings = current_user.get("settings", {})
    unlocked_levels = settings.get("unlockedLevels", {})
    
    progress_list = []
    for row in rows:
        cat = row.category or "mixed"
        total_q = (row.total_correct or 0) + (row.total_errors or 0)
        acc = (row.total_correct / total_q * 100) if total_q > 0 else 0
        avg_time = (row.total_time_seconds / row.total_games) if row.total_games > 0 else 0
        
        progress_list.append({
            "category": cat,
            "unlocked_level": unlocked_levels.get(cat, 0),
            "total_games": row.total_games or 0,
            "total_score": row.total_score or 0,
            "total_correct": row.total_correct or 0,
            "total_errors": row.total_errors or 0,
            "total_time_seconds": row.total_time_seconds or 0,
            "accuracy_rate": round(acc, 2),
            "avg_response_time": round(avg_time, 2)
        })
    return progress_list

@app.patch("/users/me/progress/level")
async def update_user_level(
    level_update: CategoryLevelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    settings = user.settings or {}
    unlocked_levels = settings.get("unlockedLevels", {})
    
    current_level = unlocked_levels.get(level_update.category, 0)
    
    if level_update.new_level > current_level:
        unlocked_levels[level_update.category] = level_update.new_level
        settings["unlockedLevels"] = unlocked_levels
        
        from sqlalchemy.orm.attributes import flag_modified
        user.settings = settings
        flag_modified(user, "settings")
        await db.commit()
    
    return {"message": "Nivel actualizado", "unlockedLevels": unlocked_levels}

@app.post("/users")
async def save_user(
    user_data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    # Security check
    if current_user["role"] != "ADMIN" and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="No permission to update this user")
    
    # Fetch existing user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Update allowed fields
    if current_user["role"] != "ADMIN":
        # Non-admins can only update certain fields
        allowed = ["username", "avatar", "settings"]
        for key in allowed:
            if key in user_data:
                setattr(user, key, user_data[key])
    else:
        # Admins can update more
        for key in ["username", "avatar", "settings", "role", "status", "unlocked_level"]:
            if key in user_data:
                setattr(user, key, user_data[key])
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "avatar": user.avatar,
        "unlocked_level": user.unlocked_level
    }

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "Usuario eliminado correctamente", "id": user_id}

# Admin: Create user with password
class AdminUserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "USER"

@app.post("/admin/users")
async def admin_create_user(
    user_data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Admin-only: Create a new user with password."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Create user with hashed password
    user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        status="ACTIVE"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "message": "Usuario creado correctamente"
    }

# Admin: Change user password
class PasswordChange(BaseModel):
    new_password: str

@app.patch("/admin/users/{user_id}/password")
async def admin_change_password(
    user_id: str,
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Admin-only: Change a user's password."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Update password
    user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Contraseña actualizada correctamente", "user_id": user_id}

# ==================== SCORES ====================

@app.get("/scores")
async def get_scores(
    user: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = select(Score)
    if user:
        query = query.where(Score.user_id == user)
    
    result = await db.execute(query)
    scores = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "score": s.score,
            "correct_count": s.correct_count,
            "error_count": s.error_count,
            "avg_time": s.avg_time,
            "date": s.date.isoformat() if s.date else None,
            "category": s.category,
            "difficulty": s.difficulty
        }
        for s in scores
    ]

@app.post("/scores")
async def save_score(
    record: ScoreRecord,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    new_score = Score(
        user_id=current_user["id"],
        score=record.score,
        correct_count=record.correctCount,
        error_count=record.errorCount,
        avg_time=record.avgTime,
        category=record.category,
        difficulty=record.difficulty
    )
    
    db.add(new_score)
    await db.commit()
    await db.refresh(new_score)
    
    return {
        "id": new_score.id,
        "score": new_score.score,
        "message": "Score guardado exitosamente"
    }

@app.delete("/scores")
async def delete_all_scores(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await db.execute(delete(Score).where(Score.user_id == current_user["id"]))
    await db.commit()
    return {"message": "Historial eliminado correctamente"}

@app.delete("/scores/{score_id}")
async def delete_score_by_id(
    score_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Score).where(Score.id == score_id))
    score = result.scalar_one_or_none()
    
    if not score:
        raise HTTPException(status_code=404, detail="Puntuación no encontrada")
    
    if score.user_id != current_user["id"] and current_user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="No tienes permiso")
    
    await db.delete(score)
    await db.commit()
    
    return {"message": "Puntuación eliminada", "id": score_id}

# ==================== AVATAR ====================

@app.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes")

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        image = ImageOps.fit(image, (500, 500), method=Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=80, optimize=True)
        buffer.seek(0)
        
        file_extension = "webp"
        content_type = "image/webp"
        
    except Exception as img_err:
        print(f"Image processing failed: {img_err}")
        raise HTTPException(status_code=422, detail="Error procesando la imagen.")

    filename = f"{current_user['id']}_{uuid.uuid4()}.{file_extension}"
    
    if not all([S3_ACCESS_KEY, S3_SECRET_KEY, S3_ENDPOINT_URL, S3_BUCKET_NAME]):
        raise HTTPException(status_code=503, detail="Configuración S3 incompleta.")
    
    try:
        s3 = boto3.client('s3',
                          endpoint_url=S3_ENDPOINT_URL,
                          aws_access_key_id=S3_ACCESS_KEY,
                          aws_secret_access_key=S3_SECRET_KEY,
                          region_name=S3_REGION)

        s3.upload_fileobj(
            buffer,
            S3_BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': content_type}
        )
        
        # Devolver una URL que pase por nuestro propio API
        # Traefik interceptará /api y lo enviará aquí
        url = f"/api/avatars/{filename}"
        return {"success": True, "url": url}
        
    except Exception as e:
        print(f"S3 Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {str(e)}")

@app.get("/avatars/{filename}")
async def get_avatar(filename: str):
    """Proxy para servir las imágenes de MinIO sin exponer el bucket a internet"""
    if not all([S3_ACCESS_KEY, S3_SECRET_KEY, S3_ENDPOINT_URL, S3_BUCKET_NAME]):
        raise HTTPException(status_code=503, detail="Configuración S3 incompleta.")
    
    try:
        s3 = boto3.client('s3',
                          endpoint_url=S3_ENDPOINT_URL,
                          aws_access_key_id=S3_ACCESS_KEY,
                          aws_secret_access_key=S3_SECRET_KEY,
                          region_name=S3_REGION)
        
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=filename)
        return StreamingResponse(response['Body'], media_type="image/webp")
        
    except s3.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="Avatar no encontrado")
    except Exception as e:
        print(f"Error fetching avatar {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo imagen")
