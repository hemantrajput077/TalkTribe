# TalkTribe - Language Exchange Platform

A real-time language exchange platform built with FastAPI, React, PostgreSQL, and WebRTC.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git

### Setup Instructions

1. **Clone the repository** (if not already done)
   ```bash
   git clone <your-repo-url>
   cd TalkTribe
   ```

2. **Create environment file**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and change passwords if needed
   ```

3. **Start all services**
   ```bash
   docker-compose up --build
   ```

4. **Access the applications**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

### Testing the Setup

1. Open http://localhost:5173 in your browser
2. Click "Test API Connection" button
3. You should see "✓ Connected: healthy"

## 📦 Project Structure

```
TalkTribe/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database connection
│   │   └── core/           # Core functionality
│   ├── tests/              # Backend tests
│   └── Dockerfile.dev      # Development Docker image
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.tsx         # Main React component
│   │   ├── main.tsx        # React entry point
│   │   └── config/         # Frontend configuration
│   └── Dockerfile.dev      # Development Docker image
└── docker-compose.yml      # Docker services configuration
```

## 🛠️ Development Commands

### Docker Commands
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild services
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backend Commands (inside container)
```bash
# Enter backend container
docker-compose exec backend bash

# Run tests
pytest

# Check code style
black .
isort .
flake8 .
```

### Frontend Commands (inside container)
```bash
# Enter frontend container
docker-compose exec frontend sh

# Run linter
npm run lint
```

## 📚 Current Status

**Milestone 1.1: Project Setup & Infrastructure** ✅ COMPLETE

- ✅ Docker environment configured
- ✅ PostgreSQL database running
- ✅ Redis cache running
- ✅ FastAPI backend with health checks
- ✅ React frontend with Tailwind CSS
- ✅ All services communicating

**Next: Milestone 1.2 - Database Models & Migrations**

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Kill the process or change ports in docker-compose.yml
```

### Docker Issues
```bash
# Clean restart
docker-compose down -v
docker-compose up --build

# Check Docker is running
docker ps
```

### Can't Connect to API
1. Check backend logs: `docker-compose logs backend`
2. Verify backend is healthy: http://localhost:8000/health
3. Check CORS settings in `backend/app/config.py`

## 📖 Documentation

- Architecture: See [ARCHITECTURE.md](./ARCHITECTURE.md)
- Milestones: See [MILESTONES.md](./MILESTONES.md)
- Learning Guide: See [claude.md](./claude.md)

## 🎯 Learning Resources

This project is built with a learning-first approach. Check these files:
- `backend/app/main.py` - Detailed comments on FastAPI setup
- `backend/app/config.py` - Configuration management patterns
- `backend/app/database.py` - Async SQLAlchemy setup
- `frontend/src/App.tsx` - React with TypeScript example

---

**Built with ❤️ for learning backend development**
