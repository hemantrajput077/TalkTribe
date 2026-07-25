# Quick Reference Guide

## 🚀 Common Commands

### Docker
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild and start
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart a service
docker-compose restart backend

# Enter a container
docker-compose exec backend bash
docker-compose exec frontend sh
docker-compose exec postgres psql -U talktribe -d talktribe_db
docker-compose exec redis redis-cli
```

### Backend Commands (inside backend container)
```bash
# Enter backend container
docker-compose exec backend bash

# Run tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Format code
black .
isort .

# Lint code
flake8 .

# Type check
mypy .

# Database migrations (later)
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend Commands (inside frontend container)
```bash
# Enter frontend container
docker-compose exec frontend sh

# Install new package
npm install package-name

# Run linter
npm run lint

# Build for production
npm run build
```

### PostgreSQL Commands
```bash
# Connect to database
docker-compose exec postgres psql -U talktribe -d talktribe_db

# Inside psql:
\l              # List databases
\dt             # List tables
\d table_name   # Describe table
\du             # List users
\q              # Quit

# Run SQL from host
docker-compose exec postgres psql -U talktribe -d talktribe_db -c "SELECT * FROM users;"
```

### Redis Commands
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Inside redis-cli:
PING                    # Test connection
KEYS *                  # List all keys
GET key_name            # Get value
SET key_name value      # Set value
DEL key_name            # Delete key
FLUSHALL                # Delete all keys (careful!)
exit
```

---

## 📁 Project Structure

```
TalkTribe/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database connection
│   │   ├── core/                # Core functionality
│   │   ├── models/              # Database models (ORM)
│   │   ├── schemas/             # Pydantic schemas (validation)
│   │   ├── api/                 # API routes
│   │   ├── services/            # Business logic
│   │   └── utils/               # Utilities
│   ├── tests/                   # Tests
│   ├── alembic/                 # Database migrations
│   ├── pyproject.toml           # Dependencies
│   ├── Dockerfile.dev           # Development Docker image
│   └── .env                     # Environment variables (don't commit!)
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # React entry point
│   │   ├── App.tsx              # Main component
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Route pages
│   │   ├── services/            # API clients
│   │   ├── store/               # State management
│   │   ├── hooks/               # Custom hooks
│   │   ├── types/               # TypeScript types
│   │   └── config/              # Configuration
│   ├── public/                  # Static files
│   ├── package.json             # Dependencies
│   ├── Dockerfile.dev           # Development Docker image
│   └── .env                     # Environment variables (don't commit!)
├── docs/                        # Documentation
├── docker-compose.yml           # Services configuration
└── .env                         # Global environment variables
```

---

## 🔗 Important URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React app |
| Backend API | http://localhost:8000 | FastAPI endpoints |
| API Docs (Swagger) | http://localhost:8000/api/docs | Interactive API docs |
| API Docs (ReDoc) | http://localhost:8000/api/redoc | Alternative docs |
| PostgreSQL | localhost:5432 | Database (use client) |
| Redis | localhost:6379 | Cache (use client) |

---

## 🔧 Troubleshooting

### Service Won't Start
```bash
# Check if port is already in use
netstat -ano | findstr :8000    # Windows
lsof -i :8000                   # Mac/Linux

# Check Docker is running
docker ps

# Check service logs
docker-compose logs backend
```

### Code Changes Not Reflecting
```bash
# Backend auto-reload should work, check logs for errors
docker-compose logs -f backend

# Frontend hot reload should work
# If not, restart the service
docker-compose restart frontend
```

### Database Connection Issues
```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Check connection from backend
docker-compose exec backend python -c "from app.database import engine; print('OK')"

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Permission Issues (Windows)
```bash
# Run as Administrator
# Or check Docker Desktop settings → Resources → File Sharing
```

### Out of Disk Space
```bash
# Clean up unused Docker resources
docker system prune

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune
```

---

## 📝 Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 🧪 Testing Checklist

- [ ] Docker Desktop is running
- [ ] All services start: `docker-compose up`
- [ ] Backend health check: http://localhost:8000/health
- [ ] Frontend loads: http://localhost:5173
- [ ] API docs accessible: http://localhost:8000/api/docs
- [ ] Frontend can connect to backend (click test button)
- [ ] No errors in logs: `docker-compose logs`

---

## 🎯 Development Workflow

1. **Start services**
   ```bash
   docker-compose up
   ```

2. **Make code changes** (hot reload is enabled)
   - Backend: Edit files in `backend/`
   - Frontend: Edit files in `frontend/src/`

3. **Check logs** if something breaks
   ```bash
   docker-compose logs -f backend
   ```

4. **Test changes**
   - Backend: http://localhost:8000/api/docs
   - Frontend: http://localhost:5173

5. **Run tests** (later)
   ```bash
   docker-compose exec backend pytest
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```

---

## 🐛 Common Error Messages

### "Address already in use"
**Solution**: Port is taken, change it in docker-compose.yml or kill the process

### "Cannot connect to the Docker daemon"
**Solution**: Start Docker Desktop

### "Network talktribe declared as external, but could not be found"
**Solution**: Run `docker-compose down` then `docker-compose up`

### "Module not found" (Backend)
**Solution**: Rebuild container `docker-compose up --build backend`

### "Cannot find module" (Frontend)
**Solution**: Delete node_modules and rebuild `docker-compose up --build frontend`

### CORS error in browser
**Solution**: Check `BACKEND_CORS_ORIGINS` includes your frontend URL

---

## 📚 Key Files to Remember

### When you need to...

**Add Python dependency**:
- Edit: `backend/pyproject.toml`
- Rebuild: `docker-compose up --build backend`

**Add npm package**:
- Edit: `frontend/package.json`
- Rebuild: `docker-compose up --build frontend`

**Change API configuration**:
- Edit: `backend/app/config.py`

**Change environment variables**:
- Edit: `.env` files
- Restart: `docker-compose restart`

**Add new API route**:
- Create: `backend/app/api/v1/your_route.py`
- Register in: `backend/app/main.py`

**Add new React page**:
- Create: `frontend/src/pages/YourPage.tsx`
- Add route in: `frontend/src/router.tsx` (later)

---

## 💡 Pro Tips

1. **Keep Docker Desktop running** while developing
2. **Check logs first** when something breaks
3. **Use API docs** (http://localhost:8000/api/docs) to test endpoints
4. **Don't commit .env files** (they contain secrets)
5. **Rebuild after dependency changes** (`--build` flag)
6. **Use `docker-compose down -v` carefully** (deletes database!)
