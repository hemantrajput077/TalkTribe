from fastapi import APIRouter

from app.domains.auth.api.routes import router as auth_router

router = APIRouter()
router.include_router(auth_router)
