# TalkTribe - Development Milestones

This document breaks down the development into small, testable, production-ready milestones.

Each milestone follows this structure:
- **Why this comes first**: Dependencies and reasoning
- **Files to create**: Complete file list
- **Folder structure**: Organization
- **APIs to build**: Endpoints and functionality
- **Testing checklist**: How to verify completion

---

# Phase 1: Foundation

## Milestone 1.1: Project Setup & Infrastructure

### Why this comes first
This is the foundation. Without proper project structure, Docker setup, and configuration management, we can't build anything else. This milestone ensures:
- Consistent development environment across machines
- Proper dependency management
- Configuration best practices
- Basic health checks work

### Files to create

#### Root Level
```
TalkTribe/
├── .gitignore
├── .env.example
├── docker-compose.yml
├── docker-compose.dev.yml
├── README.md
└── Makefile (optional, for common commands)
```

#### Backend
```
backend/
├── .env.example
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── pytest.ini
├── Dockerfile
├── Dockerfile.dev
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── core/
│       ├── __init__.py
│       └── exceptions.py
└── tests/
    ├── __init__.py
    └── conftest.py
```

#### Frontend
```
frontend/
├── .env.example
├── .gitignore
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── Dockerfile
├── Dockerfile.dev
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── vite-env.d.ts
│   └── config/
│       └── constants.ts
└── public/
```

### Detailed Implementation

#### 1. Root `.gitignore`
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/

# Node
node_modules/
dist/
.npm
.eslintcache

# Environment
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Docker
*.log
docker-compose.override.yml

# Database
*.db
*.sqlite
postgres_data/
redis_data/
```

#### 2. Root `.env.example`
```env
# Database
POSTGRES_USER=talktribe
POSTGRES_PASSWORD=change_this_in_production
POSTGRES_DB=talktribe_db
DATABASE_URL=postgresql+asyncpg://talktribe:change_this_in_production@localhost:5432/talktribe_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=change_this_to_a_long_random_string_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
API_V1_PREFIX=/api/v1

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

#### 3. `docker-compose.yml`
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: talktribe_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-talktribe}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: ${POSTGRES_DB:-talktribe_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-talktribe}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - talktribe

  redis:
    image: redis:7-alpine
    container_name: talktribe_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - talktribe

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: talktribe_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-talktribe}:${POSTGRES_PASSWORD:-changeme}@postgres:5432/${POSTGRES_DB:-talktribe_db}
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-dev_secret_key_change_in_production}
      JWT_ALGORITHM: ${JWT_ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      REFRESH_TOKEN_EXPIRE_DAYS: ${REFRESH_TOKEN_EXPIRE_DAYS:-7}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - talktribe

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: talktribe_frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
      VITE_WS_URL: ${VITE_WS_URL:-ws://localhost:8000}
    depends_on:
      - backend
    networks:
      - talktribe

volumes:
  postgres_data:
  redis_data:

networks:
  talktribe:
    driver: bridge
```

#### 4. Backend `pyproject.toml`
```toml
[tool.poetry]
name = "talktribe-backend"
version = "0.1.0"
description = "TalkTribe Language Exchange Platform - Backend API"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"
asyncpg = "^0.29.0"
psycopg2-binary = "^2.9.9"
redis = "^5.0.1"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.6"
pydantic = {extras = ["email"], version = "^2.5.3"}
pydantic-settings = "^2.1.0"
websockets = "^12.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
httpx = "^0.26.0"
black = "^23.12.1"
isort = "^5.13.2"
flake8 = "^7.0.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

#### 5. Backend `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="TalkTribe API",
    description="Language Exchange Platform API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to TalkTribe API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",  # We'll implement actual checks later
        "redis": "connected"
    }

@app.get("/api/v1/ping")
async def ping():
    return {"message": "pong"}
```

#### 6. Backend `app/config.py`
```python
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "TalkTribe"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### 7. Backend `app/database.py`
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### 8. Backend `Dockerfile.dev`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Command will be overridden by docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### 9. Frontend `package.json`
```json
{
  "name": "talktribe-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "@tanstack/react-query": "^5.17.19",
    "zustand": "^4.5.0",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.19.0",
    "@typescript-eslint/parser": "^6.19.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12"
  }
}
```

#### 10. Frontend `vite.config.ts`
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    watch: {
      usePolling: true
    }
  }
})
```

#### 11. Frontend `tailwind.config.js`
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

#### 12. Frontend `src/main.tsx`
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

#### 13. Frontend `src/App.tsx`
```typescript
import { useState } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')

  const checkAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      const data = await response.json()
      setApiStatus(`Connected: ${data.status}`)
    } catch (error) {
      setApiStatus('API Unavailable')
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold text-blue-600 mb-4">
          TalkTribe
        </h1>
        <p className="text-gray-600 mb-4">
          Language Exchange Platform
        </p>
        <button 
          onClick={checkAPI}
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
        >
          Check API Connection
        </button>
        <p className="mt-4 text-sm text-gray-500">
          Status: {apiStatus}
        </p>
      </div>
    </div>
  )
}

export default App
```

#### 14. Frontend `src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
```

#### 15. Frontend `Dockerfile.dev`
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application
COPY . .

# Expose port
EXPOSE 5173

# Start dev server
CMD ["npm", "run", "dev"]
```

### Testing Checklist

#### Step 1: Environment Setup
```bash
# Copy environment file
cp .env.example .env

# Edit .env and set secure passwords
```

#### Step 2: Start Services
```bash
# Build and start all services
docker-compose up --build

# Or start in detached mode
docker-compose up -d --build
```

#### Step 3: Verify Database Connection
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Connect to PostgreSQL
docker-compose exec postgres psql -U talktribe -d talktribe_db

# Inside psql:
# \l  (list databases)
# \q  (quit)
```

#### Step 4: Verify Redis Connection
```bash
# Check Redis is running
docker-compose ps redis

# Connect to Redis
docker-compose exec redis redis-cli

# Inside redis-cli:
# PING  (should return PONG)
# exit
```

#### Step 5: Verify Backend API
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test ping endpoint
curl http://localhost:8000/api/v1/ping

# Open API documentation
# Visit: http://localhost:8000/api/docs
```

#### Step 6: Verify Frontend
```bash
# Open browser
# Visit: http://localhost:5173

# Click "Check API Connection" button
# Should show "Connected: healthy"
```

#### Step 7: Check Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f backend
```

#### Step 8: Verify Docker Volumes
```bash
# List volumes
docker volume ls | grep talktribe

# Should see:
# - talktribe_postgres_data
# - talktribe_redis_data
```

### Success Criteria

✅ **All services start without errors**
- [ ] PostgreSQL container is healthy
- [ ] Redis container is healthy
- [ ] Backend starts and connects to both DB and Redis
- [ ] Frontend starts and can reach backend

✅ **API endpoints respond correctly**
- [ ] `GET /health` returns 200 with status "healthy"
- [ ] `GET /api/v1/ping` returns "pong"
- [ ] API documentation accessible at `/api/docs`

✅ **Frontend loads and connects**
- [ ] React app loads in browser
- [ ] "Check API Connection" button works
- [ ] Shows "Connected: healthy" status

✅ **Docker networking works**
- [ ] Services can communicate via service names
- [ ] Ports are correctly mapped to host
- [ ] Volumes persist data

### Common Issues & Solutions

**Issue**: Port already in use
```bash
# Check what's using the port
lsof -i :8000  # Backend port
lsof -i :5432  # PostgreSQL port
lsof -i :6379  # Redis port
lsof -i :5173  # Frontend port

# Kill the process or change ports in docker-compose.yml
```

**Issue**: Database connection fails
```bash
# Check if DATABASE_URL is correct in .env
# Ensure postgres service is healthy
docker-compose ps postgres

# Restart services
docker-compose restart backend
```

**Issue**: Frontend can't reach backend
```bash
# Check CORS settings in backend/app/config.py
# Verify VITE_API_URL in frontend .env
# Check browser console for CORS errors
```

**Issue**: Changes not reflecting
```bash
# Backend: Auto-reload should work with --reload flag
# Frontend: Vite HMR should work automatically

# If not working, rebuild:
docker-compose down
docker-compose up --build
```

### Cleanup Commands
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove all containers, networks, and images
docker-compose down --rmi all

# Start fresh
docker-compose up --build --force-recreate
```

---

## Milestone 1.2: Database Models & Migrations

### Why this comes after 1.1
Now that we have infrastructure running, we need to define our data models and set up Alembic for database migrations. This must come before authentication because auth depends on the User model.

### Files to create
```
backend/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── (migrations will be generated here)
├── app/
│   └── models/
│       ├── __init__.py
│       ├── base.py
│       ├── user.py
│       ├── language.py
│       ├── user_language.py
│       ├── friendship.py
│       ├── message.py
│       ├── call.py
│       └── refresh_token.py
```

### Detailed Implementation

#### 1. `app/models/base.py`
```python
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr
from app.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class UUIDMixin:
    """Mixin for UUID primary key"""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

#### 2. `app/models/user.py`
```python
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin, UUIDMixin
from app.database import Base

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(500))
    country = Column(String(100))
    timezone = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    languages = relationship("UserLanguage", back_populates="user", cascade="all, delete-orphan")
    sent_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan"
    )
    received_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.addressee_id",
        back_populates="addressee",
        cascade="all, delete-orphan"
    )
    sent_messages = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_messages = relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )
    initiated_calls = relationship(
        "Call",
        foreign_keys="Call.caller_id",
        back_populates="caller",
        cascade="all, delete-orphan"
    )
    received_calls = relationship(
        "Call",
        foreign_keys="Call.callee_id",
        back_populates="callee",
        cascade="all, delete-orphan"
    )
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.username}>"
```

#### 3. `app/models/language.py`
```python
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin
from app.database import Base

class Language(Base, TimestampMixin):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # ISO 639-1
    name = Column(String(100), nullable=False)  # English name
    native_name = Column(String(100))  # Native name
    
    # Relationships
    user_languages = relationship("UserLanguage", back_populates="language")
    
    def __repr__(self):
        return f"<Language {self.code}: {self.name}>"
```

#### 4. `app/models/user_language.py`
```python
from sqlalchemy import Column, Integer, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin, UUIDMixin
from app.database import Base
import enum

class ProficiencyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    FLUENT = "fluent"
    NATIVE = "native"

class UserLanguage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_languages"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    language_id = Column(Integer, ForeignKey("languages.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_level = Column(Enum(ProficiencyLevel), nullable=False)
    is_native = Column(Boolean, default=False, index=True)
    is_learning = Column(Boolean, default=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="languages")
    language = relationship("Language", back_populates="user_languages")
    
    def __repr__(self):
        return f"<UserLanguage user={self.user_id} lang={self.language_id}>"
```

#### 5. `app/models/friendship.py`
```python
from sqlalchemy import Column, Enum, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin, UUIDMixin
from app.database import Base
import enum

class FriendshipStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class Friendship(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "friendships"
    
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    addressee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(FriendshipStatus), default=FriendshipStatus.PENDING, index=True)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="sent_friend_requests")
    addressee = relationship("User", foreign_keys=[addressee_id], back_populates="received_friend_requests")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('requester_id != addressee_id', name='check_not_self'),
        UniqueConstraint('requester_id', 'addressee_id', name='unique_friendship'),
    )
    
    def __repr__(self):
        return f"<Friendship {self.requester_id} -> {self.addressee_id}: {self.status}>"
```

#### 6. `app/models/message.py`
```python
from sqlalchemy import Column, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin, UUIDMixin
from app.database import Base

class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"
    
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('sender_id != receiver_id', name='check_not_self_message'),
    )
    
    def __repr__(self):
        return f"<Message {self.sender_id} -> {self.receiver_id}>"
```

#### 7. `app/models/call.py`
```python
from sqlalchemy import Column, Integer, Enum, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin, UUIDMixin
from app.database import Base
import enum

class CallType(str, enum.Enum):
    VOICE = "voice"
    VIDEO = "video"

class CallStatus(str, enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    ENDED = "ended"
    MISSED = "missed"
    REJECTED = "rejected"

class Call(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "calls"
    
    caller_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    callee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    call_type = Column(Enum(CallType), nullable=False)
    status = Column(Enum(CallStatus), default=CallStatus.INITIATED)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Relationships
    caller = relationship("User", foreign_keys=[caller_id], back_populates="initiated_calls")
    callee = relationship("User", foreign_keys=[callee_id], back_populates="received_calls")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('caller_id != callee_id', name='check_not_self_call'),
    )
    
    def __repr__(self):
        return f"<Call {self.caller_id} -> {self.callee_id}: {self.status}>"
```

#### 8. `app/models/refresh_token.py`
```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimestampMixin, UUIDMixin
from app.database import Base

class RefreshToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken user={self.user_id}>"
```

#### 9. `app/models/__init__.py`
```python
from app.models.user import User
from app.models.language import Language
from app.models.user_language import UserLanguage, ProficiencyLevel
from app.models.friendship import Friendship, FriendshipStatus
from app.models.message import Message
from app.models.call import Call, CallType, CallStatus
from app.models.refresh_token import RefreshToken

__all__ = [
    "User",
    "Language",
    "UserLanguage",
    "ProficiencyLevel",
    "Friendship",
    "FriendshipStatus",
    "Message",
    "Call",
    "CallType",
    "CallStatus",
    "RefreshToken",
]
```

#### 10. `alembic/env.py`
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import settings and models
from app.config import settings
from app.database import Base
from app.models import *  # Import all models

# this is the Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### 11. `alembic.ini` (update)
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Testing Checklist

#### Step 1: Initialize Alembic
```bash
# Enter backend container
docker-compose exec backend bash

# Initialize Alembic (if not already done)
# Note: This should already be set up, just verify
ls alembic/
```

#### Step 2: Create Initial Migration
```bash
# Inside backend container
alembic revision --autogenerate -m "Initial migration: create all tables"

# This will create a new migration file in alembic/versions/
```

#### Step 3: Review Migration
```bash
# Check the generated migration file
# It should create all tables: users, languages, user_languages, 
# friendships, messages, calls, refresh_tokens

# File will be at: alembic/versions/XXXX_initial_migration.py
```

#### Step 4: Run Migration
```bash
# Apply the migration
alembic upgrade head

# Check current version
alembic current

# Should show the latest migration
```

#### Step 5: Verify Tables in PostgreSQL
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U talktribe -d talktribe_db

# List all tables
\dt

# Expected tables:
# - users
# - languages
# - user_languages
# - friendships
# - messages
# - calls
# - refresh_tokens
# - alembic_version

# Check users table structure
\d users

# Check indexes
\di

# Exit psql
\q
```

#### Step 6: Seed Language Data
Create a seed script to populate languages:

```bash
# Create backend/app/scripts/seed_languages.py
```

```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import Language

LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "de", "name": "German", "native_name": "Deutsch"},
    {"code": "it", "name": "Italian", "native_name": "Italiano"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
    {"code": "zh", "name": "Chinese", "native_name": "中文"},
    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
]

async def seed_languages():
    async with AsyncSessionLocal() as session:
        for lang_data in LANGUAGES:
            language = Language(**lang_data)
            session.add(language)
        
        await session.commit()
        print(f"Seeded {len(LANGUAGES)} languages")

if __name__ == "__main__":
    asyncio.run(seed_languages())
```

```bash
# Run the seed script
docker-compose exec backend python app/scripts/seed_languages.py
```

#### Step 7: Verify Seed Data
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U talktribe -d talktribe_db

# Check languages
SELECT * FROM languages;

# Should show 12 languages
# Exit
\q
```

### Success Criteria

✅ **Database schema created**
- [ ] All 7 tables exist in PostgreSQL
- [ ] All indexes are created
- [ ] All constraints are applied
- [ ] Alembic version table tracks migration

✅ **Models work correctly**
- [ ] All models import without errors
- [ ] Relationships are properly defined
- [ ] Enums are correctly configured

✅ **Migrations work**
- [ ] Initial migration creates all tables
- [ ] `alembic upgrade head` runs successfully
- [ ] `alembic current` shows correct version
- [ ] Can rollback: `alembic downgrade -1`

✅ **Seed data loaded**
- [ ] 12 languages exist in database
- [ ] All language codes are unique
- [ ] Names and native names are correct

### Common Issues & Solutions

**Issue**: Alembic can't find models
```python
# Make sure all models are imported in alembic/env.py
from app.models import *
```

**Issue**: Migration doesn't detect changes
```bash
# Force autogenerate to detect everything
alembic revision --autogenerate -m "description"

# Check if models are imported correctly
# Ensure Base.metadata includes all tables
```

**Issue**: Foreign key constraints fail
```bash
# Make sure parent tables are created first
# Check the order in alembic migration file
# PostgreSQL requires referenced tables to exist
```

**Issue**: Enum types already exist
```bash
# If re-running migrations, drop the database first
docker-compose down -v
docker-compose up -d postgres
# Then re-run migrations
```

---

## What's Next?

After completing Milestone 1.2, we'll move to:

**Milestone 1.3: Authentication System**
- JWT implementation
- Password hashing
- Login/Register endpoints
- Token refresh mechanism

Would you like me to continue with the next milestones, or should we pause here so you can implement 1.1 and 1.2 first?

I recommend implementing these first two milestones before continuing, so you have a solid foundation and can test as you go.
