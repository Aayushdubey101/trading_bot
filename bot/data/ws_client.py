import asyncio
import json
import logging
from typing import List

import websockets

from ..core.config import settings
from ..core.event_bus import EventBus
from ..core.events import Event, EventType

logger = logging.getLogger("BinanceWebSocket")


class BinanceWebsocketClient:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._running  = False
        self._task     = None
        self._ws       = None

    async def connect_and_listen(self, streams: List[str]):
        """
        Connect to Binance Futures Testnet combined stream.

        FIX: Correct combined-stream URL format is:
          wss://stream.binancefuture.com/stream?streams=btcusdt@ticker/ethusdt@ticker
        NOT:
          wss://stream.binancefuture.com/ws/btcusdt@ticker/ethusdt@ticker
        """
        stream_param = "/".join(streams)
        url = f"wss://stream.binancefuture.com/stream?streams={stream_param}"

        self._running = True
        while self._running:
            try:
                logger.info("Connecting to WS: %s", url)
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    self._ws = ws
                    logger.info("Connected to Binance Futures Testnet WebSocket.")
                    while self._running:
                        msg  = await ws.recv()
                        data = json.loads(msg)
                        # Combined stream wraps payload in {"stream": ..., "data": {...}}
                        payload = data.get("data", data)
                        await self.event_bus.publish(
                            Event(type=EventType.MARKET_DATA, data=payload)
                        )
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket closed. Reconnecting in 3 s…")
                await asyncio.sleep(3)
            except Exception as exc:
                logger.error("WebSocket error: %s. Reconnecting in 5 s…", exc)
                await asyncio.sleep(5)

    def start(self, streams: List[str]):
        if not self._task:
            self._task = asyncio.create_task(self.connect_and_listen(streams))

    async def stop(self):
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
