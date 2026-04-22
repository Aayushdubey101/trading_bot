from typing import Dict, Any
from enum import Enum
from pydantic import BaseModel

class EventType(str, Enum):
    MARKET_DATA = "MARKET_DATA"
    SIGNAL = "SIGNAL"
    ORDER_REQUEST = "ORDER_REQUEST"
    ORDER_FILLED = "ORDER_FILLED"
    ERROR = "ERROR"
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"

class Event(BaseModel):
    type: EventType
    data: Dict[str, Any]
