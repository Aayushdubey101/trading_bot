from typing import Dict, Any

class OrderBook:
    """In-memory representation of market state (price, depth)."""
    
    def __init__(self):
        # Symbol -> latest price
        self.prices: Dict[str, float] = {}
        # Symbol -> depth data
        self.depth: Dict[str, Any] = {}

    def update_price(self, symbol: str, price: float):
        self.prices[symbol] = price

    def update_depth(self, symbol: str, depth_data: Any):
        self.depth[symbol] = depth_data

    def get_price(self, symbol: str) -> float:
        return self.prices.get(symbol, 0.0)

# Global orderbook instance
order_book = OrderBook()
