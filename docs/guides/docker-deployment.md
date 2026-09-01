# Docker & Deployment Guide — TalkTribe

## What is Docker and Why We Use It

**The Problem Without Docker:**
- You install Python 3.11, PostgreSQL, Redis locally
- Your teammate has Python 3.10, different OS, different PostgreSQL version
- "It works on my machine" — the classic nightmare

**What Docker Solves:**
- Packages your entire app (code + runtime + OS libraries) into a container
- That container runs identically everywhere — your laptop, teammate's laptop, a server in the cloud
- Think of a container as a lightweight, isolated "mini-computer" that only has exactly what your app needs

---

## Files Already in Place

### `backend/Dockerfile.dev` and `backend/Dockerfile`

Recipes that tell Docker how to build the backend image.

```
FROM python:3.11-slim         # Start from official Python image (pre-built Linux + Python)
WORKDIR /app                  # All commands run inside /app directory
RUN apt-get install gcc ...   # Install system-level libraries Python packages need
COPY pyproject.toml .         # Copy only the dependency manifest first
RUN pip install -e .          # Install all Python deps (cached separately)
COPY . .                      # Now copy the actual code
EXPOSE 8000                   # Document which port the app uses
CMD uvicorn app.main:app ...  # The command to start the server
```

**Why copy `pyproject.toml` first, THEN the code?**

Docker builds in layers. Each RUN/COPY creates a layer. If nothing changed in a layer,
Docker reuses its cache. So when you change a .py file:
- Layer 1 (system deps): cached
- Layer 2 (pyproject.toml + pip install): cached (you didn't change dependencies)
- Layer 3 (COPY . .): rebuilds here only

**Difference between dev and prod Dockerfiles:**
- Dev: `CMD uvicorn ... --reload` — reloads when code changes
- Prod: `CMD alembic upgrade head && uvicorn ...` — runs DB migrations first, then starts

### `frontend/Dockerfile.dev` and `frontend/Dockerfile` (partially done)

Same concept for Node/React.
- Dev runs `npm run dev` (Vite dev server with hot reload)
- PROBLEM: Production uses `npm run preview` — this is Vite's toy server, not suitable for production
- NEEDS: Multi-stage build with Nginx (see "What's Missing" section below)

### `docker-compose.yml`

Orchestrates all 4 containers with one command: `docker compose up`

Key concepts:
- `volumes: ./backend:/app` — Mounts your local folder INTO the container. Edit a .py file on
  your laptop, the container sees it instantly. This is why dev works with --reload.
- `depends_on: postgres: condition: service_healthy` — Backend won't start until PostgreSQL
  passes its healthcheck. Without this, backend crashes on startup because DB isn't ready.
- `networks: talktribe` — All containers share a private network. Inside backend container,
  use `postgres` (service name) as hostname, not `localhost`. Docker DNS resolves it.
- `healthcheck` — Docker periodically runs a test command inside the container.
  `pg_isready -U talktribe` checks if PostgreSQL is accepting connections.

### `.dockerignore`

Like .gitignore but for Docker. When `COPY . .` runs, ignores .git/, node_modules/, .venv/
so they don't bloat the image.

---

## How Development Currently Works (The Flow)

```
You run: docker compose up

Docker reads docker-compose.yml
  -> Pulls postgres:15-alpine and redis:7-alpine from Docker Hub
  -> Builds talktribe_backend from backend/Dockerfile.dev
  -> Builds talktribe_frontend from frontend/Dockerfile.dev
  -> Creates private network "talktribe"
  -> Starts postgres, waits for healthcheck to pass
  -> Starts redis, waits for healthcheck to pass
  -> Starts backend (backend code mounted live from your disk)
  -> Starts frontend (frontend code mounted live from your disk)

You visit http://localhost:5173        -> React app
React calls http://localhost:8000/api  -> FastAPI
FastAPI connects to postgres:5432      -> PostgreSQL (Docker internal DNS)
FastAPI connects to redis:6379         -> Redis (Docker internal DNS)
```

Your local disk edits -> instant reload in both backend and frontend.

---

## Development vs Production — Key Differences

| Aspect            | Development                          | Production                              |
|-------------------|--------------------------------------|-----------------------------------------|
| Code mounting     | volumes: ./backend:/app (live)       | Code baked INTO the image (no mounting) |
| Frontend          | Vite dev server on port 5173         | Nginx serves built static files on :80  |
| API proxy         | Browser hits localhost:8000 directly | Nginx reverse-proxies /api to backend   |
| SSL/HTTPS         | Not needed                           | Required (Let's Encrypt)                |
| Secrets           | .env on your laptop                  | Secrets manager or encrypted env files  |
| Migrations        | Run manually or on startup           | Must run before new version starts      |

---

## What's Missing for Production

### 1. Multi-stage Frontend Dockerfile

The current production Dockerfile uses `npm run preview` (Vite's built-in preview server).
This is wrong for production because:
- Single-threaded, can't handle real traffic
- No gzip compression
- No caching headers for static assets
- Can't handle SSL

**What we need:** A multi-stage Dockerfile:
- Stage 1 (Builder): Node image compiles React -> outputs /dist folder
- Stage 2 (Final): Nginx image copies /dist and serves it

The Node runtime is NOT included in the final image — the compiled JS/HTML/CSS is all Nginx needs.
This makes the final image tiny (~20MB vs ~400MB).

### 2. Nginx Configuration (`nginx.conf`)

Nginx needs to:
- Serve static files from `/usr/share/nginx/html` (the compiled React build)
- Proxy any request to `/api/*` to `http://backend:8000` (the backend container)
- Return `index.html` for any unknown route (so React Router works correctly)
- Handle gzip compression and caching headers

### 3. `docker-compose.prod.yml`

A separate compose file for production with:
- No volume mounts (code is baked into images)
- Nginx service added (exposes port 80/443 to internet)
- Backend/PostgreSQL/Redis NOT exposed to internet (internal network only)
- Real environment variable values (from secrets, not defaults)
- Backend healthcheck so frontend Nginx starts only after backend is healthy

### 4. GitHub Actions CI/CD Pipeline (`.github/workflows/deploy.yml`)

Automatically triggered when you push to main branch:
1. Run pytest (backend tests)
2. Build backend Docker image
3. Build frontend Docker image (multi-stage)
4. Push images to Docker registry (Docker Hub or GitHub Container Registry)
5. SSH into production server
6. Pull new images
7. `docker compose -f docker-compose.prod.yml up -d`
8. Run database migrations

---

## The Production Architecture (After We Build It)

```
Internet
    |
    v
[Nginx :80/:443]   <- Only this port exposed to internet
    |-- /          -> serves compiled React files (static HTML/CSS/JS)
    |-- /api/*     -> reverse proxy to http://backend:8000

[Backend :8000]    <- Internal only, not reachable from internet
    |-- connects to postgres:5432
    |-- connects to redis:6379

[PostgreSQL :5432] <- Internal only
[Redis :6379]      <- Internal only
```

Security insight: Only Nginx's port 80/443 is exposed to the internet.
PostgreSQL, Redis, and the backend live on the internal Docker network only.

## The Production Deployment Flow

```
git push origin main
        |
        v
GitHub Actions triggers
  -> Run tests (pytest)
  -> Build backend image -> push to registry
  -> Build frontend image (Node build + Nginx) -> push to registry
        |
        v
SSH into VPS (DigitalOcean / AWS EC2 / etc.)
  -> docker pull latest images
  -> docker compose -f docker-compose.prod.yml up -d
  -> alembic upgrade head (run new migrations)
        |
        v
Live at https://yourdomain.com
```

---

## The 5 Things We Need to Implement

1. **Multi-stage frontend `Dockerfile`** — Builder stage (Node) compiles React, final stage (Nginx) serves it
2. **`nginx.conf`** — Serve static files + reverse proxy `/api` to backend + React Router support
3. **`docker-compose.prod.yml`** — Production orchestration: no volume mounts, adds Nginx, correct env vars
4. **Backend healthcheck in compose** — So Nginx starts only after backend is fully up
5. **`.github/workflows/deploy.yml`** — GitHub Actions: test -> build -> push -> SSH deploy

---

## Key Concepts to Know for Interviews

**Docker layers and caching** — Why we copy dependency files before source code.

**Multi-stage builds** — How to keep production images small by throwing away the build toolchain.

**Reverse proxy** — Nginx receiving requests and forwarding them to another service internally.
This is the standard pattern for all production web apps.

**Health checks** — How containers signal readiness so dependent services don't start too early.

**Docker networking** — Containers on the same network use service names as hostnames.
Outside traffic reaches only the ports you explicitly expose.

**Immutable infrastructure** — In production, you don't edit code on the server.
You build a new image, push it, and replace the running container. This makes deployments
reproducible and rollbacks easy (just run the previous image tag).
