from fastapi import FastAPI, APIRouter

from routers import health

from app import main


router = APIRouter()

@router.post("/")
def start():
    main()


app = FastAPI()
app.include_router(health.router)
app.include_router(router)
