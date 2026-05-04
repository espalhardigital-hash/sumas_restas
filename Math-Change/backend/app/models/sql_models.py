from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True) # UUID from Auth (or auto-gen)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)  # For local auth
    role = Column(String, default="USER")
    status = Column(String, default="ACTIVE")
    avatar = Column(String, nullable=True)
    settings = Column(JSON, default={})
    unlocked_level = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True) # Auto-increment ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=False)
    error_count = Column(Integer, nullable=False)
    avg_time = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    category = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
