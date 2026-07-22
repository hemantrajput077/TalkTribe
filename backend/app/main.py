from fastapi import FastAPI

from app.db.base import Base
from app.db.database import engine
from app.models.auth import *

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Talk Tribe"}