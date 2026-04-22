import asyncio
import logging
from typing import Dict, Any

from ..core.config import settings
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

logger = logging.getLogger("RiskEngine")


class RiskEngine:
    def __init__(self, event_bus: EventBus):
        self.event_bus        = event_bus
        self.max_position_size = settings.max_position_size
        self.max_leverage      = settings.max_leverage
        self.positions: Dict[str, float] = {}
        self.event_bus.subscribe(EventType.SIGNAL,       self.on_signal)
        self.event_bus.subscribe(EventType.ORDER_FILLED, self.on_order_filled)

    async def on_signal(self, event: Event):
        signal = event.data
        passed, reason = self.validate_signal(signal)
        if passed:
            logger.info("Signal validated for %s → forwarding to execution.", signal["symbol"])
            await self.event_bus.publish(Event(type=EventType.ORDER_REQUEST, data=signal))
        else:
            # FIX: publish an ERROR event so the API can surface rejection reason to caller
            logger.warning("Signal REJECTED by risk engine: %s — reason: %s", signal, reason)
            await self.event_bus.publish(Event(
                type=EventType.ERROR,
                data={"reason": reason, "signal": signal},
            ))

    def validate_signal(self, signal: Dict[str, Any]) -> tuple[bool, str]:
        """
        Returns (True, "") if valid, (False, reason_string) if rejected.
        FIX: returns reason so API can forward it to the caller.
        """
        symbol   = signal.get("symbol", "")
        quantity = float(signal.get("quantity", 0))
        side     = signal.get("side", "")

        if quantity <= 0:
            return False, f"Invalid quantity {quantity} — must be > 0"

        if side not in ("BUY", "SELL"):
            return False, f"Invalid side '{side}' — must be BUY or SELL"

        current = self.positions.get(symbol, 0.0)
        delta   = quantity if side == "BUY" else -quantity
        if abs(current + delta) > self.max_position_size:
            return False, (
                f"Would exceed max position size {self.max_position_size} "
                f"for {symbol} (current={current}, delta={delta})"
            )

        return True, ""

    async def on_order_filled(self, event: Event):
        """Keep position tracking in sync with filled orders."""
        data   = event.data
        symbol = data.get("symbol", "")
        qty    = float(data.get("executedQty", 0))
        side   = data.get("side", "")
        if symbol:
            current = self.positions.get(symbol, 0.0)
            self.positions[symbol] = current + (qty if side == "BUY" else -qty)
            logger.debug("Position updated | %s → %.4f", symbol, self.positions[symbol])

    def update_position(self, symbol: str, size: float):
        self.positions[symbol] = size
