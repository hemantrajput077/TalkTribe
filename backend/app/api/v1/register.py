from fastapi import APIRouter, Depends , status
from app.schemas.auth import CreateUser  , RegisterResponse
from app.services.auth_service import AuthService
from app.db.dependencies import get_db
from app.db.session import SessionLocal
from app.models.auth import User
from fastapi import HTTPException  
from sqlalchemy import select
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse,
    status_code=201)
def user_register( user_data:CreateUser, db: SessionLocal = Depends(get_db) , ): 
    auth_service = AuthService(db,user_data)
    if  auth_service.check_username_exist(user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if auth_service.check_email_exist(user_data.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User()
    user.username = user_data.username
    user.email = user_data.email
    user.password = user_data.password
    user.full_name = user_data.full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete(
    "/users/{id}",
    status_code=status.HTTP_200_OK
)
def delete_user(
    id: int,
    db: SessionLocal
     = Depends(get_db)
):
    user = db.execute(
        select(User).where(User.id == id)
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {
        "success": True,
        "message": "User deleted successfully"
    }
     