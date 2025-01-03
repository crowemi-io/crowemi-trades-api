import json

from fastapi import APIRouter, status

from models.order import Order
from trader import Trader
from common.helper import Helper

TRADER = Trader()

router = APIRouter(
    prefix="/v1/order",
    tags=["order"]
)

@router.get("/{order_id}")
async def get_order(order_id: str):

    return status.HTTP_401_UNAUTHORIZED

@router.get("/")
async def get_order():
    return status.HTTP_401_UNAUTHORIZED

@router.patch("/profit/{order_id}")
async def update(order_id: str):
    return status.HTTP_401_UNAUTHORIZED 

@router.get("/profit/")
async def get_profit():
    records = [Order.from_mongo(record) for record in TRADER.mongo_client.read("order", {"sell_status": "filled"})]
    return Helper.calculate_profit(records)

@router.get("/position/")
async def get_position():
    ret = Trader().alpaca_trading_client.get_positions()
    return ret

@router.get("/feed/")
async def get_feed():
    ret = list()
    orders = [Order().from_mongo(record) for record in TRADER.mongo_client.read("order", {})]
    # id: 1,
    # content: 'Bought 0.08728136 @229.144',
    # target: 'AAPL',
    # href: 'https://finance.yahoo.com/quote/AAPL/',
    # date: 'Nov 11',
    # datetime: '2024-11-22',
    # icon: PlusCircleIcon,
    # iconBackground: 'bg-green-500',
    for order in orders:
        # buy order
        ret.append({
            "id": str(order.buy_order_id),
            "type": "buy", 
            "content": f"Bought {order.quantity}@{order.buy_price}", 
            "target": order.symbol, 
            "date": order.buy_at_utc.strftime("%b %d"), 
            "datetime": order.buy_at_utc.strftime("%Y-%m-%d"),
            "sort_key": order.buy_at_utc,
        })
        # sell order
        if order.sell_order_id:
            ret.append({
                "id": str(order.sell_order_id), 
                "type": "sell",
                "content": f"Sold {order.quantity}@{order.sell_price}; Profit: {order.profit}", 
                "target": order.symbol, 
                "date": order.sell_at_utc.strftime("%b %d"), 
                "datetime": order.sell_at_utc.strftime("%Y-%m-%d"),
                "sort_key": order.sell_at_utc,
            })
    ret.sort(key=lambda x: x["sort_key"], reverse=True)
    [record.pop("sort_key") for record in ret]
    return json.dumps(ret[0:10])