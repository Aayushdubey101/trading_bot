from pydantic import BaseModel, ConfigDict
from typing import Optional

class OrderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    symbol: str
    side: str
    order_type: str
    status: str
    orig_qty: float
    executed_qty: float
    avg_price: Optional[float] = None
    price: Optional[float] = None
