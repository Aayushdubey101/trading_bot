from fastapi import FastAPI
import asyncio
import logging
from ..core.config import settings
from ..core.event_bus import EventBus
from ..core.db import Database
from ..client.async_client import BinanceAsyncClient
from ..data.ws_client import BinanceWebsocketClient
from ..risk.risk_manager import RiskEngine
from ..execution.executor import ExecutionEngine
from ..strategy.mean_reversion import MeanReversionStrategy
from ..strategy.momentum import MomentumStrategy
from . import routes

logger = logging.getLogger("FastAPIServer")

app = FastAPI(title="Quant Trading System", version="1.0.0")

class AppState:
    def __init__(self):
        self.event_bus = EventBus()
        self.db = Database(self.event_bus)
        self.client = BinanceAsyncClient()
        self.ws_client = BinanceWebsocketClient(self.event_bus)
        self.risk_engine = RiskEngine(self.event_bus)
        self.execution_engine = ExecutionEngine(self.event_bus, self.client)
        
        # Initialize strategies
        self.mean_reversion = MeanReversionStrategy(self.event_bus)
        self.momentum = MomentumStrategy(self.event_bus)

state = AppState()

# Inject dependencies into router
routes.db_instance = state.db
routes.event_bus_instance = state.event_bus
routes.client_instance = state.client

app.include_router(routes.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up system components...")
    
    # Init DB
    await state.db.init_db()
    
    # Start Event Bus
    state.event_bus.start()
    
    # Start WebSockets (example streams for BTC and ETH)
    state.ws_client.start(["btcusdt@ticker", "ethusdt@ticker"])
    
    logger.info("System components started successfully.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down system components...")
    await state.ws_client.stop()
    await state.event_bus.stop()
    await state.client.close()
    logger.info("System shut down complete.")
