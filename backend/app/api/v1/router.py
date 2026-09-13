from fastapi import APIRouter

from app.domains.auth.api.routes import router as auth_router
from app.domains.profile.api.interest_routes import interests_router, profiles_interests_router
from app.domains.profile.api.routes import router as profile_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(interests_router)
router.include_router(profiles_interests_router)
