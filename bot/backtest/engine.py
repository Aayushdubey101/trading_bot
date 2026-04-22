import logging
from typing import List, Dict, Any
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

logger = logging.getLogger("BacktestEngine")

class BacktestEngine:
    """Engine for replaying historical data and evaluating strategies."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.historical_data: List[Dict[str, Any]] = []
        
    def load_data(self, data: List[Dict[str, Any]]):
        self.historical_data = data
        logger.info(f"Loaded {len(data)} records for backtesting.")
        
    async def run(self):
        logger.info("Starting backtest...")
        for row in self.historical_data:
            event = Event(type=EventType.MARKET_DATA, data=row)
            await self.event_bus.publish(event)
        logger.info("Backtest completed.")
