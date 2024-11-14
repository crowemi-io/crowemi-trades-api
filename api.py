import logging
from fastapi import FastAPI, APIRouter
from routers import health
from app import main

logging.basicConfig(level=logging.WARNING)


router = APIRouter()

@router.post("/")
def start():
    if main():
        return {"Status": "Success"}
    else:
        return {"Status": "Failure"}


app = FastAPI()
app.include_router(health.router)
app.include_router(router)
