# Milestone 1.1: Project Setup & Infrastructure - Complete Explanation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Root Configuration Files](#root-configuration-files)
3. [Backend Configuration](#backend-configuration)
4. [Backend Application Files](#backend-application-files)
5. [Frontend Configuration](#frontend-configuration)
6. [Frontend Application Files](#frontend-application-files)
7. [How Everything Works Together](#how-everything-works-together)
8. [Testing Guide](#testing-guide)

---

## Overview

### What We Built
We created a complete development environment using Docker containers for:
- **PostgreSQL**: Our main database
- **Redis**: For caching and real-time features
- **FastAPI Backend**: Python web API
- **React Frontend**: User interface

### Why This Architecture?
1. **Docker**: Everyone gets the exact same environment (no "works on my machine" problems)
2. **Separation of Concerns**: Frontend, backend, and databases run independently
3. **Easy to Scale**: Can add more containers later
4. **Production-Ready**: Same setup works in development and production

---

## Root Configuration Files

### 1. `.gitignore`
**What**: Tells Git which files/folders to ignore  
**Why**: Keeps secrets, temporary files, and dependencies out of version control

```gitignore
# Python cache files
__pycache__/
*.pyc

# Node modules (very large)
node_modules/

# Environment files (contain secrets)
.env
.env.local

# Database files (shouldn't be in Git)
postgres_data/
redis_data/
```

**Key Concept**: Never commit `.env` files or `node_modules/` to Git!

---

### 2. `.env` and `.env.example`
**What**: Environment variables for configuration  
**Why**: Keeps secrets separate from code

`.env.example` → Template (commit to Git)  
`.env` → Actual secrets (never commit)

```env
# Database credentials
POSTGRES_USER=talktribe
POSTGRES_PASSWORD=changeme  # Change in production!

# JWT Secret (used for authentication tokens)
JWT_SECRET_KEY=dev_secret_key_change_in_production
```

**Interview Concept**:
- **Environment Variables**: Configuration that changes between environments (dev/staging/prod)
- **Security**: Never hardcode passwords in source code
- **12-Factor App**: Store config in environment (industry standard)

---

### 3. `docker-compose.yml` ⭐ IMPORTANT

**What**: Defines all our Docker services and how they connect  
**Why**: One command (`docker-compose up`) starts everything

Let's break down each service:

#### Service 1: PostgreSQL Database
```yaml
postgres:
  image: postgres:15-alpine           # Which Docker image to use
  container_name: talktribe_postgres  # Name for this container
  environment:                        # Environment variables
    POSTGRES_USER: ${POSTGRES_USER:-talktribe}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
  volumes:                            # Persist data between restarts
    - postgres_data:/var/lib/postgresql/data
  ports:                              # Map container port to host
    - "5432:5432"
  healthcheck:                        # Check if database is ready
    test: ["CMD-SHELL", "pg_isready -U talktribe"]
    interval: 10s
```

**Key Concepts**:
- **Volumes**: Data persists even when container stops
- **Ports**: `host:container` format (5432:5432 means localhost:5432 → container:5432)
- **Healthcheck**: Other services wait for database to be "healthy"
- **${VAR:-default}**: Use environment variable VAR, or "default" if not set

#### Service 2: Redis Cache
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes  # Enable persistence
  volumes:
    - redis_data:/data
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

**Why Redis?**
- In-memory data store (super fast)
- We'll use it for: sessions, WebSocket connections, caching, rate limiting

#### Service 3: Backend (FastAPI)
```yaml
backend:
  build:
    context: ./backend              # Where to find Dockerfile
    dockerfile: Dockerfile.dev      # Which Dockerfile to use
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  volumes:
    - ./backend:/app               # Mount code (changes reflect immediately)
  environment:
    DATABASE_URL: postgresql+asyncpg://talktribe:changeme@postgres:5432/talktribe_db
  depends_on:                      # Wait for these services first
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**Key Concepts**:
- **Volume Mount**: `./backend:/app` means local `backend/` folder → container `/app`
- **Hot Reload**: Code changes reflect immediately (no restart needed)
- **Service Names**: Use `postgres` and `redis` as hostnames (Docker DNS)
- **depends_on**: Backend waits for database to be healthy before starting

#### Service 4: Frontend (React)
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile.dev
  command: npm run dev
  volumes:
    - ./frontend:/app
    - /app/node_modules           # Don't overwrite container's node_modules
  ports:
    - "5173:5173"
  environment:
    VITE_API_URL: http://localhost:8000
```

**Key Concept**: 
- Two volumes: one for code, one for node_modules
- `VITE_` prefix required for environment variables in Vite

#### Networks and Volumes
```yaml
volumes:
  postgres_data:    # Named volume (Docker manages location)
  redis_data:

networks:
  talktribe:        # All services on same network
    driver: bridge
```

---

### 4. `.dockerignore`
**What**: Tells Docker what to exclude when building images  
**Why**: Faster builds, smaller images

```dockerignore
**/__pycache__       # Python cache
**/node_modules      # Don't copy into image (will install fresh)
**/.env              # Don't bake secrets into image
```

---

## Backend Configuration

### 1. `pyproject.toml` ⭐ IMPORTANT

**What**: Python project configuration and dependencies (using Poetry)  
**Why**: Manages dependencies and ensures everyone has same versions

```toml
[tool.poetry.dependencies]
python = "^3.11"                                    # Python version
fastapi = "^0.109.0"                               # Web framework
uvicorn = {extras = ["standard"], version = "^0.27.0"}  # ASGI server
sqlalchemy = "^2.0.25"                             # ORM (database)
alembic = "^1.13.1"                                # Database migrations
asyncpg = "^0.29.0"                                # Async PostgreSQL driver
redis = "^5.0.1"                                   # Redis client
python-jose = {extras = ["cryptography"], version = "^3.3.0"}  # JWT
passlib = {extras = ["bcrypt"], version = "^1.7.4"}  # Password hashing
pydantic = {extras = ["email"], version = "^2.5.3"}  # Data validation
websockets = "^12.0"                               # WebSocket support
```

**Key Dependencies Explained**:

1. **FastAPI**: Modern Python web framework
   - Automatic API documentation
   - Type hints for validation
   - Async support (non-blocking I/O)

2. **Uvicorn**: ASGI server
   - Runs FastAPI application
   - Handles HTTP requests
   - `--reload` flag for development

3. **SQLAlchemy**: ORM (Object-Relational Mapping)
   - Write Python instead of SQL
   - Handles database connections
   - Supports relationships

4. **Alembic**: Database migrations
   - Version control for database schema
   - Track changes over time
   - Easy rollback

5. **AsyncPG**: PostgreSQL driver
   - Non-blocking database operations
   - Better performance than psycopg2

6. **Redis**: In-memory data store client

7. **Python-Jose**: JWT (JSON Web Tokens)
   - Create authentication tokens
   - Verify user identity

8. **Passlib + Bcrypt**: Password hashing
   - Never store plain passwords
   - Industry-standard hashing

9. **Pydantic**: Data validation
   - Validate request data
   - Automatic type conversion
   - Clear error messages

**Development Dependencies**:
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"           # Testing framework
pytest-asyncio = "^0.23.3"  # Async test support
httpx = "^0.26.0"          # HTTP client for testing
black = "^23.12.1"         # Code formatter
isort = "^5.13.2"          # Import sorter
flake8 = "^7.0.0"          # Linter
```

---

### 2. `Dockerfile.dev`

**What**: Instructions to build backend Docker image  
**Why**: Consistent Python environment for everyone

```dockerfile
FROM python:3.11-slim    # Base image (minimal Python)

WORKDIR /app             # Set working directory

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \                # C compiler (needed for some Python packages)
    postgresql-client \  # PostgreSQL command-line tools
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency file
COPY pyproject.toml ./

# Install dependencies
RUN poetry config virtualenvs.create false \  # Install globally
    && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

EXPOSE 8000             # Document which port the app uses

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Key Concepts**:
- **Layers**: Each `RUN` command creates a layer (cached for faster builds)
- **Order Matters**: Copy dependencies first (changes less often than code)
- **`--host 0.0.0.0`**: Listen on all interfaces (needed in Docker)
- **`--reload`**: Auto-restart on code changes (development only)

---

## Backend Application Files

### 1. `app/config.py` ⭐ IMPORTANT

**What**: Centralized configuration using Pydantic Settings  
**Why**: Type-safe configuration with validation

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "TalkTribe"
    
    # CORS (which origins can access our API)
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Database
    DATABASE_URL: str  # Required (no default)
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",      # Load from .env file
        case_sensitive=True   # POSTGRES_USER != postgres_user
    )

settings = Settings()  # Create global instance
```

**How It Works**:
1. Pydantic reads `.env` file
2. Validates types (int, str, List, etc.)
3. Uses defaults if not provided
4. Raises error if required field missing

**Interview Concepts**:
- **Settings Management**: Single source of truth for configuration
- **Type Safety**: Catch config errors at startup, not runtime
- **Environment-based**: Different values for dev/staging/prod

---

### 2. `app/database.py` ⭐ IMPORTANT

**What**: Database connection and session management  
**Why**: Provides database access to route handlers

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,           # Log all SQL queries
    pool_size=10,        # Keep 10 connections ready
    max_overflow=20,     # Allow 20 more if needed
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)

# Base class for ORM models
Base = declarative_base()

# Dependency for routes
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session           # Provide session to route
            await session.commit()  # Commit if successful
        except Exception:
            await session.rollback()  # Rollback on error
            raise
        finally:
            await session.close()   # Always close
```

**Key Concepts**:

1. **Async Engine**: Non-blocking database operations
   - Can handle many requests simultaneously
   - Better performance under load

2. **Connection Pool**:
   - Reuses database connections
   - `pool_size=10`: Keep 10 ready
   - `max_overflow=20`: Create up to 20 more if busy

3. **Session Management**:
   - **Session**: Workspace for database operations
   - **Commit**: Save changes to database
   - **Rollback**: Undo changes on error
   - **Close**: Release connection back to pool

4. **Dependency Injection** (FastAPI pattern):
```python
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # db is automatically provided
    # automatically committed/closed after function returns
```

**Interview Question**: "What is a database connection pool?"
> A pool maintains multiple open connections to the database. Instead of opening a new connection for each request (slow), we reuse connections from the pool (fast). When done, the connection returns to the pool for reuse.

---

### 3. `app/main.py` ⭐ IMPORTANT

**What**: FastAPI application entry point  
**Why**: Creates the API, configures middleware, defines routes

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create app instance
app = FastAPI(
    title="TalkTribe API",
    docs_url="/api/docs",      # Swagger UI
    redoc_url="/api/redoc",    # Alternative docs
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to TalkTribe API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Key Concepts**:

1. **CORS (Cross-Origin Resource Sharing)**:
   - Browser security feature
   - By default, frontend on `localhost:5173` can't call API on `localhost:8000`
   - CORS middleware allows it

2. **Middleware**: Code that runs before/after every request
   - CORS middleware adds special headers
   - Later: authentication middleware, logging, etc.

3. **Async Routes**: Can handle many requests simultaneously
   ```python
   async def handler():  # Non-blocking
       await db_query()   # Other requests can run while waiting
   ```

4. **Automatic Documentation**:
   - FastAPI generates docs from your code
   - Visit `/api/docs` to see Swagger UI
   - Can test APIs directly in browser

**FastAPI Request Flow**:
```
1. Request arrives → 
2. Middleware runs (CORS, auth, etc.) → 
3. Route handler executes → 
4. Pydantic validates response → 
5. JSON response sent
```

---

### 4. `app/core/exceptions.py`

**What**: Custom exception classes  
**Why**: Consistent error handling across the application

```python
class TalkTribeException(Exception):
    """Base exception"""
    pass

class AuthenticationError(TalkTribeException):
    """User auth failed"""
    pass

class NotFoundError(TalkTribeException):
    """Resource not found"""
    pass
```

**Usage**:
```python
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await db.get_user(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    return user
```

Later we'll add exception handlers to convert these to proper HTTP responses.

---

## Frontend Configuration

### 1. `package.json`

**What**: Node.js project configuration and dependencies  
**Why**: Manages frontend dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",              // UI library
    "react-dom": "^18.2.0",          // React renderer
    "react-router-dom": "^6.21.3",   // Routing
    "@tanstack/react-query": "^5.17.19",  // Server state management
    "zustand": "^4.5.0",             // Client state management
    "axios": "^1.6.5"                // HTTP client
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",  // Vite React plugin
    "tailwindcss": "^3.4.1",           // CSS framework
    "typescript": "^5.3.3",            // TypeScript compiler
    "vite": "^5.0.12"                  // Build tool
  }
}
```

**Key Dependencies**:

1. **React**: Component-based UI library
2. **React Router**: Client-side routing (SPA)
3. **React Query**: Async data fetching + caching
4. **Zustand**: Simple state management (auth, user data)
5. **Axios**: HTTP requests to backend
6. **Vite**: Fast build tool (replaces webpack)
7. **Tailwind CSS**: Utility-first CSS framework
8. **TypeScript**: Type-safe JavaScript

---

### 2. `vite.config.ts`

**What**: Vite build tool configuration  
**Why**: Customize dev server and build process

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,       // Listen on all interfaces (Docker needs this)
    port: 5173,
    watch: {
      usePolling: true  // File watching in Docker (Windows issue)
    }
  }
})
```

**Why `usePolling: true`?**
- Docker on Windows doesn't support native file watching
- Polling checks files every few milliseconds
- Slightly slower but works reliably

---

### 3. `tsconfig.json`

**What**: TypeScript compiler configuration  
**Why**: Configure how TypeScript compiles to JavaScript

```json
{
  "compilerOptions": {
    "target": "ES2020",        // Output modern JavaScript
    "jsx": "react-jsx",        // JSX transformation
    "strict": true,            // Enable all strict type checks
    "noUnusedLocals": true,    // Error on unused variables
  }
}
```

---

### 4. `tailwind.config.js` & `postcss.config.js`

**What**: Tailwind CSS configuration  
**Why**: Configure CSS processing

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",  // Scan these files for classes
  ],
  theme: {
    extend: {},  // Custom colors, fonts, etc.
  },
}
```

Tailwind scans files for class names and generates only the CSS you use.

---

## Frontend Application Files

### 1. `src/main.tsx`

**What**: React application entry point  
**Why**: Mounts React app to DOM

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

**Flow**:
1. `index.html` loads JavaScript
2. JavaScript finds `<div id="root">`
3. React renders `<App />` inside it

---

### 2. `src/App.tsx`

**What**: Main React component  
**Why**: The first component that renders

```typescript
function App() {
  const [apiStatus, setApiStatus] = useState<string>('Not checked')

  const checkAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      const data = await response.json()
      setApiStatus(`✓ Connected: ${data.status}`)
    } catch (error) {
      setApiStatus('✗ API Unavailable')
    }
  }

  return (
    <div>
      <button onClick={checkAPI}>Test API Connection</button>
      <p>{apiStatus}</p>
    </div>
  )
}
```

**React Concepts**:
- **useState**: Reactive state (changes trigger re-render)
- **async/await**: Clean asynchronous code
- **fetch**: Browser API for HTTP requests
- **Event Handlers**: `onClick` runs when button clicked

---

### 3. `src/index.css`

**What**: Global CSS with Tailwind directives  
**Why**: Import Tailwind utilities

```css
@tailwind base;        /* Reset styles */
@tailwind components;  /* Component classes */
@tailwind utilities;   /* Utility classes */
```

---

### 4. `src/config/constants.ts`

**What**: Frontend configuration constants  
**Why**: Centralized API URLs

```typescript
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
```

**Vite Environment Variables**:
- Must start with `VITE_` prefix
- Accessed via `import.meta.env.VITE_*`
- Replaced at build time (not runtime)

---

## How Everything Works Together

### Request Flow Example: API Health Check

1. **User clicks "Test API" button** in browser
   ```
   Browser (localhost:5173)
   ```

2. **Frontend makes fetch request**
   ```typescript
   fetch('http://localhost:8000/health')
   ```

3. **Request goes through Docker network**
   ```
   Frontend Container → Backend Container
   ```

4. **Backend receives request**
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   ```

5. **FastAPI processes**
   - Checks route matches `/health`
   - Runs `health_check()` function
   - Converts return value to JSON

6. **Response sent back**
   ```json
   {"status": "healthy"}
   ```

7. **Frontend updates UI**
   ```typescript
   setApiStatus("✓ Connected: healthy")
   ```

### Complete Tech Stack Flow

```
┌─────────────────────────────────────────────────────┐
│ BROWSER                                             │
│ ┌─────────────────────────────────────────────┐   │
│ │ React App (TypeScript)                      │   │
│ │ - Components                                 │   │
│ │ - State (Zustand)                           │   │
│ │ - API calls (Axios)                         │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                    ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────┐
│ BACKEND (Docker Container)                          │
│ ┌─────────────────────────────────────────────┐   │
│ │ FastAPI                                      │   │
│ │ ┌──────────┬──────────┬──────────┐         │   │
│ │ │ Routes   │ Services │ Models   │         │   │
│ │ └──────────┴──────────┴──────────┘         │   │
│ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         ↓                              ↓
┌──────────────────┐          ┌──────────────────┐
│ PostgreSQL       │          │ Redis            │
│ (Container)      │          │ (Container)      │
│ - User data      │          │ - Sessions       │
│ - Messages       │          │ - Cache          │
└──────────────────┘          └──────────────────┘
```

---

## Testing Guide

### Step 1: Install Docker Desktop
1. Download from https://www.docker.com/products/docker-desktop/
2. Install and restart computer
3. Start Docker Desktop
4. Verify: `docker --version`

### Step 2: Start Services
```bash
# From project root
docker-compose up --build
```

**What happens**:
1. Builds backend image (installs Python packages)
2. Builds frontend image (installs npm packages)
3. Starts PostgreSQL and waits for health check
4. Starts Redis and waits for health check
5. Starts backend (waits for DB and Redis)
6. Starts frontend (waits for backend)

**First run takes 5-10 minutes** (downloads images, installs dependencies)

### Step 3: Verify Services

**Check Docker containers**:
```bash
docker ps
```
Should see 4 containers running: postgres, redis, backend, frontend

**Check Backend**:
- Open: http://localhost:8000
- Should see: `{"message": "Welcome to TalkTribe API"}`
- Open: http://localhost:8000/api/docs
- Should see: Interactive API documentation

**Check Frontend**:
- Open: http://localhost:5173
- Should see: TalkTribe landing page
- Click "Test API Connection"
- Should see: "✓ Connected: healthy"

**Check Database**:
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U talktribe -d talktribe_db

# Inside psql:
\l               # List databases
\q               # Quit
```

**Check Redis**:
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Inside redis-cli:
PING             # Should return PONG
exit
```

### Step 4: View Logs

**All services**:
```bash
docker-compose logs -f
```

**Specific service**:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Look for**:
- Backend: "Application startup complete"
- Frontend: "Local: http://localhost:5173/"
- No error messages

### Common Issues

**Port 8000 already in use**:
```bash
# Find what's using it (Windows)
netstat -ano | findstr :8000

# Kill the process or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 on host instead
```

**Frontend can't connect to backend**:
1. Check backend is running: http://localhost:8000/health
2. Check browser console for CORS errors
3. Verify `BACKEND_CORS_ORIGINS` in `backend/app/config.py`

**Changes not reflecting**:
- Backend: Should auto-reload (check logs)
- Frontend: Should auto-reload (check terminal)
- If not working: `docker-compose restart backend` or `frontend`

---

## Key Takeaways

### What You've Accomplished ✅
1. **Docker Environment**: Professional development setup
2. **FastAPI Backend**: Async Python web API with documentation
3. **React Frontend**: Modern TypeScript SPA
4. **Database Setup**: PostgreSQL with connection pooling
5. **Redis Setup**: Ready for caching and real-time features
6. **Hot Reload**: Code changes reflect immediately

### Technologies Learned
- **Docker & Docker Compose**: Container orchestration
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and settings
- **React + TypeScript**: Type-safe UI development
- **Vite**: Fast frontend build tool
- **Tailwind CSS**: Utility-first styling

### Interview Talking Points
1. **"How do you structure a full-stack project?"**
   > Separate frontend and backend services using Docker, with shared database and cache layers. This allows independent development and scaling.

2. **"What is dependency injection in FastAPI?"**
   > Functions like `get_db()` that provide resources (like database sessions) to route handlers. FastAPI automatically calls them and handles cleanup.

3. **"Why async/await in Python?"**
   > Non-blocking I/O allows handling multiple requests simultaneously. While one request waits for the database, another can process. Better performance under load.

4. **"What is CORS and why do we need it?"**
   > Browser security that blocks requests between different origins. We add CORS middleware to explicitly allow our frontend (port 5173) to call our backend (port 8000).

5. **"How do you manage configuration?"**
   > Use environment variables for secrets and environment-specific values. Pydantic Settings provides type-safe configuration with validation.

---

## Next Steps

**Milestone 1.2: Database Models & Migrations**
- Define SQLAlchemy ORM models
- Create Alembic migrations
- Set up database schema
- Seed initial data

**What We'll Learn**:
- Database relationships (one-to-many, many-to-many)
- Database migrations and version control
- ORM patterns in SQLAlchemy 2.0
- Data seeding strategies

---

**Great job completing Milestone 1.1!** 🎉

You now have a production-grade development environment. Everything is containerized, documented, and ready for building features.
