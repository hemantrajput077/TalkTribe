from app.models.auth import User
from app.db.session import SessionLocal
from sqlalchemy import select    
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def  __init__(self, db:SessionLocal,  user:User):
        self.user = user
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
        