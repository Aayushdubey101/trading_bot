# Binance Futures Testnet Trading Bot

**Author:** Aayush Dubey  
**Role Applied:** Python Developer Intern — Primetrade.ai  

A clean, production-structured Python CLI application that places **MARKET**, **LIMIT**, and **STOP_MARKET** orders on the Binance USDT-M Futures Testnet.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package metadata
│   ├── client.py            # Binance REST client (signing, retries, error handling)
│   ├── orders.py            # Order placement logic + OrderResult dataclass
│   ├── validators.py        # Pure-Python input validation (no deps)
│   ├── logging_config.py    # Centralised rotating file + console logger
│   └── cli.py               # argparse CLI entry point
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── __main__.py              # python -m trading_bot shortcut
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone / unzip

```bash
cd trading_bot
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Only one external dependency:** `requests` (+ `urllib3` for retry logic).  
> Everything else is Python stdlib.

### 4. Get Binance Futures Testnet credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Click **API Key** → generate a new key pair
4. Copy the API key and secret

### 5. Set environment variables

```bash
# Windows (Command Prompt)
set BINANCE_TESTNET_API_KEY=your_api_key_here
set BINANCE_TESTNET_API_SECRET=your_api_secret_here

# Windows (PowerShell)
$env:BINANCE_TESTNET_API_KEY="your_api_key_here"
$env:BINANCE_TESTNET_API_SECRET="your_api_secret_here"

# macOS / Linux
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

Alternatively, pass them directly via `--api-key` and `--api-secret` flags (see examples below).

---

## How to Run

All commands are run from **inside the `trading_bot/` directory**.

### Place a MARKET BUY order

```bash
python -m bot.cli place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### Place a MARKET SELL order

```bash
python -m bot.cli place --symbol ETHUSDT --side SELL --type MARKET --qty 0.01
```

### Place a LIMIT BUY order

```bash
python -m bot.cli place --symbol BTCUSDT --side BUY --type LIMIT --qty 0.001 --price 85000
```

### Place a LIMIT SELL order

```bash
python -m bot.cli place --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3500
```

### Place a STOP_MARKET order (bonus order type)

```bash
python -m bot.cli place --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --price 58000
```

### View account balances

```bash
python -m bot.cli account
```

### Pass API keys directly (without env vars)

```bash
python -m bot.cli --api-key YOUR_KEY --api-secret YOUR_SECRET place \
  --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### Adjust log verbosity

```bash
python -m bot.cli --log-level INFO place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

---

## Sample Output

```
┌── ORDER REQUEST ───────────────────────────────────────
│  Symbol         BTCUSDT
│  Side           BUY
│  Order Type     MARKET
│  Quantity       0.001
│  Price          N/A (MARKET)
└───────────────────────────────────────────────────────

┌── ORDER RESPONSE ──────────────────────────────────────
│  Order ID       4134076736
│  Client OID     x-xcKtGhcu67c4b3b5e0ae0d
│  Symbol         BTCUSDT
│  Side           BUY
│  Type           MARKET
│  Status         FILLED
│  Orig Qty       0.001
│  Executed Qty   0.001
│  Avg Price      97350.00
│  Limit Price    —
└───────────────────────────────────────────────────────

✔  Order placed successfully!
```

---

## Logging

All API requests, responses, and errors are logged to `logs/trading_bot.log`.

- **File handler:** DEBUG level, rotating (5 MB × 3 backups)
- **Console handler:** WARNING and above only (keeps CLI output clean)

Log format:
```
2025-01-15 14:22:01 | INFO     | trading_bot.orders | Placing order | symbol=BTCUSDT side=BUY type=MARKET qty=0.001 price=N/A
2025-01-15 14:22:01 | DEBUG    | trading_bot.client | → POST /fapi/v1/order | params: {'symbol': 'BTCUSDT', ...}
2025-01-15 14:22:02 | DEBUG    | trading_bot.client | ← HTTP 200 | body: {"orderId":4134076736,...}
2025-01-15 14:22:02 | INFO     | trading_bot.orders | Order accepted | orderId=4134076736 status=FILLED executedQty=0.001 avgPrice=97350.00
```

Sample log files are included in `logs/` for reference.

---

## Validation & Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Invalid symbol (not `*USDT`) | Clear error message, non-zero exit code |
| Invalid side (not BUY/SELL) | Clear error message, logged |
| LIMIT order missing price | Clear error message |
| Negative / zero quantity | Clear error message |
| Binance API error (e.g. -2019) | Parsed error code + message displayed and logged |
| Network timeout | Retried 3× with backoff; clear error on final failure |
| Non-JSON response | Logged and surfaced as error |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| `requests` only (no `python-binance`) | Full control over signing, retries, and logging; fewer hidden abstractions |
| Separate `client.py` / `orders.py` / `validators.py` / `cli.py` | Strict layer separation — testable independently |
| `OrderResult` dataclass | Decouples display logic from raw API response; easy to extend |
| Rotating file handler | Prevents unbounded log growth in long-running use |
| HMAC-SHA256 signing in `client.py` only | Keeps auth logic in one place |
| `STOP_MARKET` as bonus order type | Demonstrates extensibility of the order layer |

---

## Assumptions

1. **Testnet only** — the base URL is hardcoded to `https://testnet.binancefuture.com`. Do not use production keys.
2. Quantities must meet Binance minimum notional and lot size filters for each symbol. If your order is rejected with error `-2019` or `-1111`, adjust `--qty` accordingly (e.g. `0.001` for BTCUSDT is typically the minimum).
3. The testnet periodically resets balances — if you see balance errors, log in to the testnet portal and request a balance refresh.
4. `timeInForce` defaults to `GTC` (Good Till Cancelled) for all LIMIT orders.
