import logging
from typing import Dict, Any, List
from ..core.event_bus import EventBus
from ..core.events import Event, EventType
from .base import Strategy

logger = logging.getLogger("StrategyEngine")

class StrategyEngine:
    """Central strategy orchestrator that subscribes to MARKET_DATA and evaluates strategies."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.strategies: List[Strategy] = []
        self.event_bus.subscribe(EventType.MARKET_DATA, self.on_market_data)
        logger.info("Strategy Engine initialized.")

    def add_strategy(self, strategy: Strategy):
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.__class__.__name__}")

    async def on_market_data(self, event: Event):
        """Handle incoming market data and evaluate all strategies."""
        for strategy in self.strategies:
            try:
                # We can update this once we have backtesting
                if hasattr(strategy, "evaluate"):
                    if hasattr(strategy.evaluate, '__await__'):
                        await strategy.evaluate(event.data)
                    else:
                        strategy.evaluate(event.data)
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy.__class__.__name__}: {e}")
