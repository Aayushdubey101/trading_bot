import logging
from typing import Dict, Any
from ..core.config import settings
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

logger = logging.getLogger("RiskEngine")

class RiskEngine:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.max_position_size = settings.max_position_size
        self.max_leverage = settings.max_leverage
        
        # Keep track of positions (in a real system, sync this with Binance API)
        self.positions: Dict[str, float] = {}
        
        self.event_bus.subscribe(EventType.SIGNAL, self.on_signal)

    async def on_signal(self, event: Event):
        """Validate signal and forward to order request if safe."""
        signal = event.data
        if self.validate_signal(signal):
            logger.info(f"Signal validated for {signal['symbol']}. Forwarding to execution.")
            await self.event_bus.publish(Event(
                type=EventType.ORDER_REQUEST,
                data=signal
            ))
        else:
            logger.warning(f"Signal rejected by risk engine: {signal}")

    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Apply risk rules to a trading signal."""
        symbol = signal.get("symbol")
        quantity = signal.get("quantity", 0.0)
        
        if quantity <= 0:
            logger.warning(f"Invalid quantity {quantity}")
            return False
            
        current_position = self.positions.get(symbol, 0.0)
        
        # Example rule: check max position size
        if abs(current_position + (quantity if signal.get("side") == "BUY" else -quantity)) > self.max_position_size:
            logger.warning(f"Exceeds max position size for {symbol}")
            return False
            
        # Add more rules as needed...
        return True

    def update_position(self, symbol: str, size: float):
        self.positions[symbol] = size
