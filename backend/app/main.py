from fastapi import FastAPI
from app.db.base import Base
from app.db.database import engine
from app.models.auth import *
from .routers import router as api_router
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(api_router)

@app.get("/")
def home():
    return {"message": "Talk Tribe"}