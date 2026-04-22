"""
tests/test_risk.py
Run:  python -m pytest tests/test_risk.py -v
"""
import pytest
import asyncio
from bot.core.event_bus import EventBus
from bot.core.events import Event, EventType
from bot.risk.risk_manager import RiskEngine


@pytest.mark.asyncio
async def test_risk_rejects_zero_quantity():
    event_bus   = EventBus()
    risk_engine = RiskEngine(event_bus)
    requests    = []

    def on_request(event): requests.append(event)
    event_bus.subscribe(EventType.ORDER_REQUEST, on_request)
    event_bus.start()

    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.0},
    ))
    await asyncio.sleep(0.15)
    await event_bus.stop()

    assert len(requests) == 0, "Zero-quantity signal should be rejected"


@pytest.mark.asyncio
async def test_risk_accepts_valid_signal():
    event_bus   = EventBus()
    risk_engine = RiskEngine(event_bus)
    requests    = []

    def on_request(event): requests.append(event)
    event_bus.subscribe(EventType.ORDER_REQUEST, on_request)
    event_bus.start()

    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
    ))
    await asyncio.sleep(0.15)
    await event_bus.stop()

    assert len(requests) == 1
    assert requests[0].data["quantity"] == 0.1


@pytest.mark.asyncio
async def test_risk_rejects_invalid_side():
    event_bus   = EventBus()
    risk_engine = RiskEngine(event_bus)
    requests    = []
    errors      = []

    def on_request(event): requests.append(event)
    def on_error(event):   errors.append(event)
    event_bus.subscribe(EventType.ORDER_REQUEST, on_request)
    event_bus.subscribe(EventType.ERROR,         on_error)
    event_bus.start()

    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={"symbol": "BTCUSDT", "side": "LONG", "quantity": 0.1},
    ))
    await asyncio.sleep(0.15)
    await event_bus.stop()

    assert len(requests) == 0
    assert len(errors) == 1
    assert "side" in errors[0].data["reason"].lower()


@pytest.mark.asyncio
async def test_risk_rejects_exceeds_max_position():
    event_bus   = EventBus()
    risk_engine = RiskEngine(event_bus)
    # Default max_position_size = 1.0 — try to buy 1.5
    requests = []
    def on_request(event): requests.append(event)
    event_bus.subscribe(EventType.ORDER_REQUEST, on_request)
    event_bus.start()

    await event_bus.publish(Event(
        type=EventType.SIGNAL,
        data={"symbol": "BTCUSDT", "side": "BUY", "quantity": 1.5},
    ))
    await asyncio.sleep(0.15)
    await event_bus.stop()

    assert len(requests) == 0, "Signal exceeding max position size should be rejected"


@pytest.mark.asyncio
async def test_risk_updates_position_on_fill():
    event_bus   = EventBus()
    risk_engine = RiskEngine(event_bus)
    event_bus.start()

    await event_bus.publish(Event(
        type=EventType.ORDER_FILLED,
        data={"symbol": "BTCUSDT", "side": "BUY", "executedQty": "0.5"},
    ))
    await asyncio.sleep(0.15)
    await event_bus.stop()

    assert risk_engine.positions.get("BTCUSDT", 0) == pytest.approx(0.5)
