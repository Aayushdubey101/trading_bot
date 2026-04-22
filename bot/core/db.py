import aiosqlite
import logging
from typing import List, Optional
from .config import settings
from .models import OrderModel
from .event_bus import EventBus
from .events import Event, EventType

logger = logging.getLogger("Database")

class Database:
    def __init__(self, event_bus: EventBus):
        self.db_path = settings.db_path
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.ORDER_FILLED, self.on_order_filled)

    async def init_db(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    client_order_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    orig_qty REAL NOT NULL,
                    executed_qty REAL NOT NULL,
                    avg_price REAL,
                    price REAL
                )
            ''')
            await db.commit()
            logger.info("Database initialized successfully.")

    async def save_order(self, order: OrderModel) -> int:
        """Insert a new order into the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO orders (order_id, client_order_id, symbol, side, order_type, status, orig_qty, executed_qty, avg_price, price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.order_id, order.client_order_id, order.symbol, order.side,
                order.order_type, order.status, order.orig_qty, order.executed_qty,
                order.avg_price, order.price
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_orders(self, limit: int = 50) -> List[OrderModel]:
        """Fetch recent orders."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM orders ORDER BY id DESC LIMIT ?', (limit,))
            rows = await cursor.fetchall()
            return [OrderModel(**dict(row)) for row in rows]

    async def on_order_filled(self, event: Event):
        """Save executed orders to database automatically."""
        data = event.data
        try:
            # Safely parse Binance response fields
            order = OrderModel(
                order_id=str(data.get("orderId")),
                client_order_id=data.get("clientOrderId"),
                symbol=data.get("symbol", "UNKNOWN"),
                side=data.get("side", "UNKNOWN"),
                order_type=data.get("type", "UNKNOWN"),
                status=data.get("status", "UNKNOWN"),
                orig_qty=float(data.get("origQty", 0)),
                executed_qty=float(data.get("executedQty", 0)),
                avg_price=float(data.get("avgPrice", 0)) if data.get("avgPrice") else None,
                price=float(data.get("price", 0)) if data.get("price") else None
            )
            await self.save_order(order)
            logger.debug(f"Order saved to DB: {order.order_id}")
        except Exception as e:
            logger.error(f"Failed to save order to DB: {e}")
