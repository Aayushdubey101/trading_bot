from typing import Optional, Dict, Any
from .base import BaseStrategy
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, event_bus: EventBus, window_size: int = 100, threshold: float = 0.02):
        super().__init__("MeanReversion", event_bus)
        self.window_size = window_size
        self.threshold = threshold
        self.prices: Dict[str, list] = {}

    async def generate_signal(self, symbol: str, current_price: float, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if symbol not in self.prices:
            self.prices[symbol] = []
            
        self.prices[symbol].append(current_price)
        if len(self.prices[symbol]) > self.window_size:
            self.prices[symbol].pop(0)
            
        if len(self.prices[symbol]) < self.window_size:
            return None
            
        avg_price = sum(self.prices[symbol]) / self.window_size
        deviation = (current_price - avg_price) / avg_price
        
        if deviation > self.threshold:
            # Overbought, sell
            return {
                "strategy": self.name,
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": 0.01  # Example static quantity
            }
        elif deviation < -self.threshold:
            # Oversold, buy
            return {
                "strategy": self.name,
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0.01
            }
            
        return None
