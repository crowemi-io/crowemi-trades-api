from typing import Union

from fastapi import FastAPI, APIRouter

from app import main


router = APIRouter(
    prefix="/",
)

@router.post("/", tags=["email"])
async def send_email():
    print("Hello World")


app = FastAPI()
app.include_router(router)
