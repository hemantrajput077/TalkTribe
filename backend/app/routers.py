from app.api.v1.register import router as register_router
from fastapi import APIRouter
router = APIRouter()
router.include_router(register_router)