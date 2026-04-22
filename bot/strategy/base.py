from abc import ABC, abstractmethod
import logging
from typing import Optional, Dict, Any
from ..core.event_bus import EventBus
from ..core.events import Event, EventType
from ..data.orderbook import order_book

logger = logging.getLogger("Strategy")

class BaseStrategy(ABC):
    def __init__(self, name: str, event_bus: EventBus):
        self.name = name
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.MARKET_DATA, self.on_market_data)

    async def on_market_data(self, event: Event):
        """Handle incoming market data."""
        data = event.data
        
        # Example: parse binance tick data
        # Real implementation would parse specific stream data like @ticker or @depth
        if "s" in data and "c" in data:
            symbol = data["s"]
            price = float(data["c"])
            order_book.update_price(symbol, price)
            
            signal = await self.generate_signal(symbol, price, data)
            if signal:
                await self.event_bus.publish(Event(
                    type=EventType.SIGNAL,
                    data=signal
                ))

    @abstractmethod
    async def generate_signal(self, symbol: str, current_price: float, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate market conditions and return a signal dict if a trade should be executed.
        Returns: None if no signal, else a dict like:
        {"strategy": self.name, "symbol": symbol, "side": "BUY", "quantity": 1.0}
        """
        pass
