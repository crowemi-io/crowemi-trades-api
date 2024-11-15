import os

from fastapi import APIRouter, status

from trader import calculate_profit


router = APIRouter(
    prefix="/v1/order_batch",
    tags=["order_batch"]
)

@router.get("/", tags=["order_batch"])
async def get_orders():
    return True

async def get_order():
    return True

@router.patch("/profit/", tags=["order_batch"])
async def update(id: str):
    pass 

@router.get("/profit/", tags=["order_batch"])
async def get_profit():
    profit = calculate_profit()
    return {"profit": profit}
