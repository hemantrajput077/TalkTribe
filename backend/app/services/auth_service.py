from app.models.auth import User
from app.db.session import SessionLocal
from app.db.dependencies import get_db
from sqlalchemy import select    
from passlib.context import CryptContext
from fastapi import Depends
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def  __init__(self, db:SessionLocal):
        self.db = db

    def check_username_exist(self ,username):
        user =  self.db.execute(select(User).filter(User.username == username)).scalars().first()
        if user:
            return True
        return False

    def check_email_exist(self , email):
        user =  self.db.execute(select(User).filter(User.email == email)).scalars().first()
        if user:
            return True
        return False

    def check_phone_exist(self , phone):
        user =  self.db.execute(select(User).filter(User.phone == phone)).scalars().first()
        if user:
            return True
        return False
   
    def check_password_exist(self,password):
        password = self.db.execute(select(User).filter(User.password==password)).scalars().first()

        if password:
            return True
        else:
            return False


def auth_service_dependency(db:SessionLocal= Depends(get_db))->AuthService:
    return AuthService(db)
        