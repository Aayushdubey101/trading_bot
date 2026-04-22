"""
bot/core/validators.py
──────────────────────
Pure-Python input validation — zero external dependencies.
Used by both the CLI layer and the Streamlit dashboard.
All validators raise ValueError with a clear human-readable message.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES       = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}
SYMBOL_RE         = re.compile(r"^[A-Z]{2,20}USDT$")


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not SYMBOL_RE.match(s):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Expected a USDT-margined pair, e.g. BTCUSDT."
        )
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be BUY or SELL.")
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return t


def validate_quantity(quantity: str) -> str:
    try:
        q = Decimal(str(quantity).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if q <= 0:
        raise ValueError(f"Quantity must be > 0, got {q}.")
    return str(q)


def validate_price(price: Optional[str], order_type: str) -> Optional[str]:
    ot = order_type.strip().upper()
    if ot in ("LIMIT", "STOP_MARKET"):
        if price is None or str(price).strip() == "":
            raise ValueError(f"Price is required for {ot} orders.")
        try:
            p = Decimal(str(price).strip())
        except InvalidOperation:
            raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
        if p <= 0:
            raise ValueError(f"Price must be > 0, got {p}.")
        return str(p)
    return None  # MARKET — price ignored


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
) -> dict:
    """Run all validators and return a clean params dict. Raises ValueError on first failure."""
    return {
        "symbol":     validate_symbol(symbol),
        "side":       validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity":   validate_quantity(quantity),
        "price":      validate_price(price, order_type),
    }
