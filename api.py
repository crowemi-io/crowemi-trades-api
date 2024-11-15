import uvicorn
import logging
from fastapi import FastAPI, APIRouter
from routers import health, order_batch

from trader import trade

logging.basicConfig(level=logging.WARNING)


router = APIRouter()

@router.post("/")
def cron():
    if trade():
        return {"Status": "Success"}
    else:
        return {"Status": "Failure"}


app = FastAPI()
app.include_router(health.router)
app.include_router(order_batch.router)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
