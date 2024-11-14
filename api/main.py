from typing import Union

from fastapi import FastAPI, APIRouter

from app import main


app = FastAPI()

router = APIRouter(
    prefix="/",
)

@router.post("/", tags=["email"])
async def send_email():
    print("Hello World")
