import os

from fastapi import APIRouter, status

from data.client import DataClient

router = APIRouter(
    prefix="/v1/order_batch",
    tags=["order_batch"]
)

@router.get("/profit/", tags=["order_batch"])
async def get():
    c = DataClient(os.getenv("MONGO_URI"))
    profit = 0
    records = c.read("order", {"sell_status": "filled"})
    return {"profit": 1000, "records":records}
