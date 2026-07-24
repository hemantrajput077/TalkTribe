from fastapi import APIRouter, Depends , status
from app.schemas.auth import CreateUser  , RegisterResponse , UserLogin
from app.services.auth_service import AuthService
from app.db.dependencies import get_db
from app.db.session import SessionLocal
from app.models.auth import User
from fastapi import HTTPException  
from sqlalchemy import select
from app.services.auth_service import AuthService , auth_service_dependency
router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get('/user_data')
def user_data(db: SessionLocal = Depends(get_db)):
    user = db.execute(select(User)).scalars().all()
    print(user)
    if not user:
        return {"message": "No user found"}
    return user

@router.post("/register", response_model=RegisterResponse,
    status_code=201)
def user_register( user_data:CreateUser, db: SessionLocal = Depends(get_db) , auth_service:AuthService = Depends(auth_service_dependency) ): 
    if  auth_service.check_username_exist(user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password
    hashed_password = pwd_context.hash(user_data.password)

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password=hashed_password,
        is_active=True
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a user by ID.

    Returns success message if user found and deleted.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()

    return {
        "success": True,
        "message": "User deleted successfully"
    }
     
@router.post("/login")
def user_login( data:UserLogin , db : SessionLocal = Depends(get_db) , auth_service: AuthService = Depends(auth_service_dependency)):
    if not auth_service.check_username_exist(data.username):
        raise HTTPException(status_code=400, detail="Invlaid username")

    if not auth_service.check_password_exist(data.password):
        raise  HTTPException(status_code=400, detail="Invlaid password")
    
    return {"Login successfully"}
