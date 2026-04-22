import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator

from ..core.db import Database
from ..core.event_bus import EventBus
from ..core.events import Event, EventType
from ..core.models import OrderModel
from ..client.async_client import BinanceAsyncClient

router = APIRouter()
logger = logging.getLogger("Routes")

# Injected at startup by server.py
db_instance:        Optional[Database]           = None
event_bus_instance: Optional[EventBus]           = None
client_instance:    Optional[BinanceAsyncClient] = None

# Rejection events accumulator (ring-buffer, last 50)
_rejection_log: list = []


def get_db()        -> Database:           return db_instance
def get_event_bus() -> EventBus:           return event_bus_instance
def get_client()    -> BinanceAsyncClient: return client_instance


# ── Request / Response schemas ─────────────────────────────────────────────

class OrderRequest(BaseModel):
    symbol:   str
    side:     str
    type:     str   = "MARKET"
    quantity: float
    price:    Optional[float] = None

    @field_validator("side")
    @classmethod
    def side_upper(cls, v):
        v = v.strip().upper()
        if v not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        return v

    @field_validator("type")
    @classmethod
    def type_upper(cls, v):
        v = v.strip().upper()
        if v not in ("MARKET", "LIMIT", "STOP_MARKET"):
            raise ValueError("type must be MARKET, LIMIT, or STOP_MARKET")
        return v

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

    @field_validator("price")
    @classmethod
    def price_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("price must be > 0")
        return v


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/account")
async def get_account(client: BinanceAsyncClient = Depends(get_client)):
    try:
        return await client.get_account()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/positions")
async def get_positions(client: BinanceAsyncClient = Depends(get_client)):
    try:
        account = await client.get_account()
        return [p for p in account.get("positions", []) if float(p.get("positionAmt", 0)) != 0]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str, client: BinanceAsyncClient = Depends(get_client)):
    try:
        return await client.get_ticker_price(symbol.upper())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/open-orders")
async def get_open_orders(
    symbol: Optional[str] = None,
    client: BinanceAsyncClient = Depends(get_client),
):
    try:
        return await client.get_open_orders(symbol=symbol)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/order")
async def place_order(
    order: OrderRequest,
    event_bus: EventBus = Depends(get_event_bus),
):
    """
    Submit a manual order through the risk engine.
    FIX: listens for ERROR events to surface rejection reason — no longer silently returns 200.
    """
    if order.type == "LIMIT" and order.price is None:
        raise HTTPException(status_code=422, detail="price is required for LIMIT orders")
    if order.type == "STOP_MARKET" and order.price is None:
        raise HTTPException(status_code=422, detail="price (stop price) is required for STOP_MARKET orders")

    # Track rejections published while we wait
    rejection: dict = {}

    async def capture_rejection(event: Event):
        nonlocal rejection
        if event.data.get("signal", {}).get("symbol") == order.symbol:
            rejection = event.data

    event_bus.subscribe(EventType.ERROR, capture_rejection)

    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={
            "strategy": "MANUAL",
            "symbol":   order.symbol.upper(),
            "side":     order.side,
            "type":     order.type,
            "quantity": order.quantity,
            "price":    order.price,
        },
    ))

    # Give event bus one tick to process
    await asyncio.sleep(0.05)

    if rejection:
        raise HTTPException(status_code=400, detail=rejection.get("reason", "Order rejected by risk engine"))

    return {"status": "Signal accepted by risk engine — order queued for execution"}


@router.get("/orders")
async def get_recent_orders(db: Database = Depends(get_db)):
    try:
        return await db.get_orders()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
