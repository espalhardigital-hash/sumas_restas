-- ========================================================
-- MATH-CHANGE - Schema SQL (PostgreSQL)
-- ========================================================
-- Este script crea las tablas necesarias para la aplicación.
-- Ejecutar con: psql -U postgres -d math_change -f schema.sql
-- ========================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- Tabla de puntuaciones
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

    CONSTRAINT fk_scores_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS ix_scores_id ON scores(id);
