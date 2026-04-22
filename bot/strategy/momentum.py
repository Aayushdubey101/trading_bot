from typing import Optional, Dict, Any
from .base import BaseStrategy
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

class MomentumStrategy(BaseStrategy):
    def __init__(self, event_bus: EventBus, window_size: int = 50, momentum_threshold: float = 0.05):
        super().__init__("Momentum", event_bus)
        self.window_size = window_size
        self.momentum_threshold = momentum_threshold
        self.prices: Dict[str, list] = {}

    async def generate_signal(self, symbol: str, current_price: float, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if symbol not in self.prices:
            self.prices[symbol] = []
            
        self.prices[symbol].append(current_price)
        if len(self.prices[symbol]) > self.window_size:
            self.prices[symbol].pop(0)
            
        if len(self.prices[symbol]) < self.window_size:
            return None
            
        # Calculate momentum as % change from oldest price in window to current price
        oldest_price = self.prices[symbol][0]
        momentum = (current_price - oldest_price) / oldest_price
        
        if momentum > self.momentum_threshold:
            # Upward momentum, buy
            return {
                "strategy": self.name,
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0.01
            }
        elif momentum < -self.momentum_threshold:
            # Downward momentum, sell
            return {
                "strategy": self.name,
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": 0.01
            }
            
        return None
