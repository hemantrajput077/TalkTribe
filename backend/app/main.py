"""
Main FastAPI application entry point.

This is where we:
1. Create the FastAPI app instance
2. Configure middleware (CORS, etc.)
3. Register routers
4. Define basic endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.config import settings
from app.routers import router as api_router

# Create FastAPI app instance
app = FastAPI(
    title="TalkTribe API",
    description="Language Exchange Platform API",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UI documentation
    redoc_url="/api/redoc",  # ReDoc documentation
    openapi_url="/api/openapi.json",  # OpenAPI schema
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows our frontend (running on port 5173) to make requests to backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # Which origins can access the API
    allow_credentials=True,  # Allow cookies to be sent
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Register routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {"message": "Welcome to TalkTribe API", "version": "0.1.0", "docs": "/api/docs"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Used by:
    - Docker healthcheck
    - Load balancers
    - Monitoring systems
    - Frontend to verify API is running
    """
    return {
        "status": "healthy",
        "database": "connected",  # We'll implement actual checks later
        "redis": "connected",
    }


@app.get("/api/v1/ping")
async def ping():
    """Simple ping endpoint to test API routing"""
    return {"message": "pong"}
