import asyncio
import json
import websockets
import logging
from typing import List, Callable, Any
from ..core.config import settings
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

logger = logging.getLogger("BinanceWebSocket")

class BinanceWebsocketClient:
    def __init__(self, event_bus: EventBus):
        self.ws_url = settings.binance_ws_url
        self.event_bus = event_bus
        self._running = False
        self._task = None
        self._ws = None

    async def connect_and_listen(self, streams: List[str]):
        """Connect to Binance WebSocket and listen for messages."""
        stream_str = "/".join(streams)
        url = f"{self.ws_url}/{stream_str}"
        
        self._running = True
        while self._running:
            try:
                logger.info(f"Connecting to WS: {url}")
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    logger.info("Connected to Binance WebSocket")
                    while self._running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        
                        # Route message to event bus
                        event = Event(type=EventType.MARKET_DATA, data=data)
                        await self.event_bus.publish(event)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed. Reconnecting...")
            except Exception as e:
                logger.error(f"WebSocket error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    def start(self, streams: List[str]):
        """Start the WebSocket in the background."""
        if not self._task:
            self._task = asyncio.create_task(self.connect_and_listen(streams))

    async def stop(self):
        """Stop the WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
