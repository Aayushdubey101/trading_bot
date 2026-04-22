import pytest
import asyncio
from bot.core.event_bus import EventBus
from bot.core.events import Event, EventType
from bot.risk.risk_manager import RiskEngine

@pytest.mark.asyncio
async def test_risk_engine_validates_quantity():
    event_bus = EventBus()
    risk_engine = RiskEngine(event_bus)
    
    # Track order requests
    requests = []
    def on_request(event):
        requests.append(event)
        
    event_bus.subscribe(EventType.ORDER_REQUEST, on_request)
    event_bus.start()
    
    # Invalid quantity should be rejected
    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.0}
    ))
    
    # Valid quantity should be accepted
    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1}
    ))
    
    await asyncio.sleep(0.1) # Let event bus process
    await event_bus.stop()
    
    assert len(requests) == 1
    assert requests[0].data["quantity"] == 0.1
