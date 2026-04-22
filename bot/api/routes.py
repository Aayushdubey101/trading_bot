from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from ..core.db import Database
from ..core.event_bus import EventBus
from ..core.events import Event, EventType
from ..core.models import OrderModel
from ..client.async_client import BinanceAsyncClient

router = APIRouter()

# Dependency injection for router (assigned during app startup)
db_instance: Database = None
event_bus_instance: EventBus = None
client_instance: BinanceAsyncClient = None

def get_db() -> Database:
    return db_instance

def get_event_bus() -> EventBus:
    return event_bus_instance

def get_client() -> BinanceAsyncClient:
    return client_instance

@router.get("/account")
async def get_account(client: BinanceAsyncClient = Depends(get_client)):
    try:
        return await client.get_account()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/positions")
async def get_positions(client: BinanceAsyncClient = Depends(get_client)):
    try:
        account_data = await client.get_account()
        positions = account_data.get("positions", [])
        return [p for p in positions if float(p.get("positionAmt", 0)) != 0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/order")
async def place_order(order: dict, event_bus: EventBus = Depends(get_event_bus)):
    """
    Submit a manual order signal. 
    It will be routed through the RiskEngine just like a strategy signal.
    """
    if "symbol" not in order or "side" not in order or "quantity" not in order:
        raise HTTPException(status_code=400, detail="Missing required fields: symbol, side, quantity")
        
    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={
            "strategy": "MANUAL",
            "symbol": order["symbol"],
            "side": order["side"],
            "type": order.get("type", "MARKET"),
            "quantity": order["quantity"],
            "price": order.get("price")
        }
    ))
    return {"status": "Signal published to event bus for risk validation"}

@router.get("/orders", response_model=List[OrderModel])
async def get_recent_orders(db: Database = Depends(get_db)):
    try:
        return await db.get_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
