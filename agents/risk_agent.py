import logging
from typing import Dict, Any
from bot.core.event_bus import EventBus
from bot.core.events import Event, EventType

logger = logging.getLogger("RiskAgent")

class RiskAgent:
    """Agent responsible for dynamic risk assessment."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.SIGNAL, self.evaluate_signal)
        
    async def evaluate_signal(self, event: Event):
        # Evaluate risk before creating ORDER_REQUEST
        logger.debug(f"Risk Agent evaluating signal: {event.data}")
