import logging
from typing import Dict, Any
from ..core.event_bus import EventBus
from ..core.events import Event, EventType
from ..client.async_client import BinanceAsyncClient

logger = logging.getLogger("ExecutionEngine")

class ExecutionEngine:
    def __init__(self, event_bus: EventBus, client: BinanceAsyncClient):
        self.event_bus = event_bus
        self.client = client
        self.event_bus.subscribe(EventType.ORDER_REQUEST, self.on_order_request)

    async def on_order_request(self, event: Event):
        """Handle validated order requests."""
        order_data = event.data
        try:
            logger.info(f"Executing order: {order_data}")
            result = await self.client.place_order(
                symbol=order_data["symbol"],
                side=order_data["side"],
                order_type=order_data["type"],
                quantity=order_data["quantity"],
                price=order_data.get("price")
            )
            
            logger.info(f"Order filled successfully: {result.get('orderId')}")
            await self.event_bus.publish(Event(
                type=EventType.ORDER_FILLED,
                data=result
            ))
            
        except Exception as e:
            logger.error(f"Failed to execute order: {e}")
            await self.event_bus.publish(Event(
                type=EventType.ERROR,
                data={"error": str(e), "order_data": order_data}
            ))
