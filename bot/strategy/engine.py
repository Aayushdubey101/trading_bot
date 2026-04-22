import logging
from typing import Dict, Any, List, Optional
from ..core.event_bus import EventBus
from ..core.events import Event, EventType
from .base import BaseStrategy          # FIX: was `Strategy` — correct name is BaseStrategy

logger = logging.getLogger("StrategyEngine")


class StrategyEngine:
    """Central strategy orchestrator — subscribes to MARKET_DATA, fans out to all strategies."""

    def __init__(self, event_bus: EventBus):
        self.event_bus  = event_bus
        self.strategies: List[BaseStrategy] = []
        self.event_bus.subscribe(EventType.MARKET_DATA, self.on_market_data)
        logger.info("StrategyEngine initialised.")

    def add_strategy(self, strategy: BaseStrategy):
        self.strategies.append(strategy)
        logger.info("Added strategy: %s", strategy.__class__.__name__)

    async def on_market_data(self, event: Event):
        """Fan out market data to every registered strategy."""
        for strategy in self.strategies:
            try:
                # FIX: BaseStrategy exposes on_market_data / generate_signal, not evaluate()
                await strategy.on_market_data(event)
            except Exception as e:
                logger.error("Error in strategy %s: %s", strategy.__class__.__name__, e)
