"""
dashboard.py
────────────
Streamlit dashboard for the Binance Futures Testnet Trading Bot.

Architecture:  Dashboard → FastAPI server (localhost:8000) → RiskEngine → ExecutionEngine → Binance

IMPORTANT: Start the API server first:
    python -m bot.cli serve

Then launch the dashboard:
    streamlit run dashboard.py

The dashboard talks to the FastAPI server via HTTP — it does NOT import
BinanceClient directly, so every order goes through the full
Risk Engine → Execution Engine pipeline.
"""

import time
from typing import Optional

import httpx
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Primetrade Bot — Testnet Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg,#0f0f23 0%,#1a1a3e 100%);
    padding:1.2rem 2rem; border-radius:12px; margin-bottom:1.5rem;
    border:1px solid #2d2d5e;
}
.main-header h1 { color:#00d4ff; margin:0; font-size:1.7rem; font-weight:700; }
.main-header p  { color:#8888aa; margin:0.3rem 0 0; font-size:0.85rem; }

.result-ok {
    background:#0a2e1a; border:1px solid #00e676; border-radius:10px;
    padding:1.1rem 1.4rem; margin-top:1rem;
}
.result-err {
    background:#2e0a0a; border:1px solid #ff5252; border-radius:10px;
    padding:1.1rem 1.4rem; margin-top:1rem;
}
.result-ok h4 { color:#00e676; margin:0 0 .7rem; }
.result-err h4 { color:#ff5252; margin:0 0 .7rem; }
.kv { display:flex; justify-content:space-between; padding:3px 0;
      border-bottom:1px solid #1a2e1a; font-size:.84rem; }
.kv .k { color:#8888aa; } .kv .v { color:#e0e0e0; font-weight:500; }

.server-ok  { color:#00e676; font-weight:600; }
.server-err { color:#ff5252; font-weight:600; }

section[data-testid="stSidebar"] { background:#0d0d1e; }

.log-box {
    background:#0a0a15; border:1px solid #2d2d5e; border-radius:8px;
    padding:1rem; font-family:'Courier New',monospace; font-size:.72rem;
    color:#a0a0c0; max-height:420px; overflow-y:auto; white-space:pre-wrap;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>📈 Primetrade.ai — Binance Futures Testnet Bot</h1>
  <p>Visual dashboard · orders route through Risk Engine → Execution Engine → Binance Testnet</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Server Connection")
    api_host = st.text_input("API Host", value="127.0.0.1")
    api_port = st.number_input("API Port", value=8000, min_value=1024, max_value=65535, step=1)
    base_url = f"http://{api_host}:{int(api_port)}"

    # Server health check
    def check_server() -> bool:
        try:
            r = httpx.get(f"{base_url}/health", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    server_up = check_server()
    if server_up:
        st.markdown('<p class="server-ok">✓ Server online</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="server-err">✗ Server offline</p>', unsafe_allow_html=True)
        st.caption(f"Start with:  `python -m bot.cli serve`")

    st.markdown("---")
    st.markdown("### 🎛️ Defaults")
    default_symbol = st.selectbox(
        "Default Symbol",
        ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"],
    )
    auto_refresh = st.toggle("Auto-refresh prices (5 s)", value=False)
    st.markdown("---")
    st.caption("Binance Futures Testnet\ntestnet.binancefuture.com")


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────

def api_get(path: str, params: dict = None) -> tuple[bool, any]:
    """Returns (ok, data_or_error_string)."""
    try:
        r = httpx.get(f"{base_url}{path}", params=params, timeout=8.0)
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("detail", r.text)
    except httpx.ConnectError:
        return False, "Cannot connect to API server. Is it running?"
    except Exception as exc:
        return False, str(exc)


def api_post(path: str, payload: dict) -> tuple[bool, any]:
    try:
        r = httpx.post(f"{base_url}{path}", json=payload, timeout=10.0)
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("detail", r.text)
    except httpx.ConnectError:
        return False, "Cannot connect to API server. Is it running?"
    except Exception as exc:
        return False, str(exc)


def _kv_rows(d: dict) -> str:
    return "".join(
        f'<div class="kv"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in d.items() if v is not None
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_place, tab_account, tab_price, tab_open, tab_history, tab_logs = st.tabs([
    "🛒 Place Order",
    "💰 Account",
    "📊 Live Prices",
    "📋 Open Orders",
    "📜 Order History",
    "📄 Logs",
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — PLACE ORDER
# ═══════════════════════════════════════════════════════════════════════════
with tab_place:
    st.subheader("Place a Futures Order")
    st.caption(
        "Orders are submitted through the **Risk Engine → Execution Engine** pipeline, "
        "not directly to Binance."
    )

    col_form, col_preview = st.columns([1.1, 1])

    with col_form:
        st.markdown("#### Order Parameters")

        symbol = st.text_input("Symbol", value=default_symbol,
                               placeholder="e.g. BTCUSDT").strip().upper()

        c1, c2 = st.columns(2)
        with c1:
            side = st.selectbox("Side", ["BUY", "SELL"])
        with c2:
            order_type = st.selectbox("Order Type", ["MARKET", "LIMIT", "STOP_MARKET"])

        quantity = st.text_input("Quantity (base asset)", value="0.001",
                                 help="e.g. 0.001 BTC for BTCUSDT")

        price_val: Optional[str] = None
        if order_type == "LIMIT":
            price_val = st.text_input("Limit Price (USDT)", placeholder="e.g. 85000")
            st.caption("Order will rest on the book at this price (GTC).")
        elif order_type == "STOP_MARKET":
            price_val = st.text_input("Stop Price (USDT)", placeholder="e.g. 58000")
            st.caption("Market order triggers when price reaches the stop level.")
        else:
            st.info("ℹ️ MARKET — fills immediately at best available price.")

        st.markdown("---")

        place_btn = st.button(
            f"🚀  Place {order_type} {side}",
            type="primary",
            use_container_width=True,
            disabled=not server_up,
        )
        if not server_up:
            st.caption("⚠️  API server must be running to place orders.")

    with col_preview:
        st.markdown("#### Live Price Reference")

        ok, ticker = api_get("/ticker/" + (symbol or "BTCUSDT"))
        if ok and isinstance(ticker, dict):
            live_p = float(ticker.get("price", 0))
            st.metric(symbol or "—", f"${live_p:,.2f}")
        else:
            st.metric(symbol or "—", "—")

        st.markdown("#### Order Preview")
        preview = {
            "Symbol":     symbol or "—",
            "Side":       side,
            "Order Type": order_type,
            "Quantity":   quantity or "—",
            "Price":      price_val or ("Market" if order_type == "MARKET" else "—"),
        }
        st.markdown(
            f'<div class="result-ok"><h4>📋 Preview</h4>{_kv_rows(preview)}</div>',
            unsafe_allow_html=True,
        )

    # ── Submit ──────────────────────────────────────────────────────────────
    if place_btn:
        # Client-side validation before hitting the server
        errors = []
        if not symbol:
            errors.append("Symbol is required.")
        if not quantity or float(quantity or 0) <= 0:
            errors.append("Quantity must be > 0.")
        if order_type in ("LIMIT", "STOP_MARKET") and not price_val:
            errors.append(f"Price is required for {order_type} orders.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            payload = {
                "symbol":   symbol,
                "side":     side,
                "type":     order_type,
                "quantity": float(quantity),
            }
            if price_val:
                payload["price"] = float(price_val)

            with st.spinner("Submitting to Risk Engine…"):
                ok, resp = api_post("/order", payload)

            if ok:
                st.balloons()
                st.markdown(
                    f'<div class="result-ok"><h4>✅ Order Accepted by Risk Engine</h4>'
                    f'<p style="color:#a0f0a0;font-size:.85rem">{resp.get("status","")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # Session history
                if "order_history" not in st.session_state:
                    st.session_state.order_history = []
                st.session_state.order_history.append({
                    "Time":     time.strftime("%H:%M:%S"),
                    "Symbol":   symbol,
                    "Side":     side,
                    "Type":     order_type,
                    "Qty":      quantity,
                    "Price":    price_val or "MARKET",
                    "Result":   "✅ Accepted",
                })
            else:
                st.markdown(
                    f'<div class="result-err"><h4>❌ Order Rejected</h4>'
                    f'<p style="color:#f08080;font-size:.85rem">{resp}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if "order_history" not in st.session_state:
                    st.session_state.order_history = []
                st.session_state.order_history.append({
                    "Time":   time.strftime("%H:%M:%S"),
                    "Symbol": symbol, "Side": side, "Type": order_type,
                    "Qty":    quantity, "Price": price_val or "MARKET",
                    "Result": f"❌ {resp}",
                })

    # Session history table
    if st.session_state.get("order_history"):
        st.markdown("---")
        st.markdown("#### Session Order Log")
        df = pd.DataFrame(st.session_state.order_history)
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Clear Session Log"):
            st.session_state.order_history = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════
with tab_account:
    st.subheader("💰 Account Balances")

    c1, _ = st.columns([1, 3])
    with c1:
        refresh_acc = st.button("🔄 Refresh", use_container_width=True,
                                disabled=not server_up, key="btn_acc")

    if not server_up:
        st.warning("Start the API server to view account data.")
    elif refresh_acc or st.session_state.get("acc_fetched"):
        with st.spinner("Fetching account…"):
            ok, data = api_get("/account")

        if not ok:
            st.error(f"Error: {data}")
        else:
            st.session_state["acc_fetched"] = True

            # Summary metrics
            assets = data.get("assets", [])
            wallet    = sum(float(a.get("walletBalance",    0)) for a in assets)
            available = sum(float(a.get("availableBalance", 0)) for a in assets)
            upnl      = sum(float(a.get("unrealizedProfit", 0)) for a in assets)

            m1, m2, m3 = st.columns(3)
            m1.metric("Wallet Balance",  f"${wallet:,.2f}")
            m2.metric("Available",       f"${available:,.2f}")
            m3.metric("Unrealised PnL",  f"${upnl:+,.2f}", delta=f"{upnl:+.4f}")

            st.markdown("---")

            # Assets table
            rows = [
                {
                    "Asset":             a["asset"],
                    "Wallet Balance":    f"{float(a.get('walletBalance',0)):,.4f}",
                    "Available":         f"{float(a.get('availableBalance',0)):,.4f}",
                    "Unrealised PnL":    f"{float(a.get('unrealizedProfit',0)):+,.4f}",
                    "Margin Balance":    f"{float(a.get('marginBalance',0)):,.4f}",
                }
                for a in assets if float(a.get("walletBalance", 0)) > 0
            ]
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No funded assets. Top up your testnet account at testnet.binancefuture.com")

            # Open positions
            positions = [p for p in data.get("positions", [])
                         if float(p.get("positionAmt", 0)) != 0]
            if positions:
                st.markdown("#### Open Positions")
                pos_rows = [{
                    "Symbol":    p["symbol"],
                    "Side":      "LONG" if float(p["positionAmt"]) > 0 else "SHORT",
                    "Size":      p["positionAmt"],
                    "Entry":     p.get("entryPrice", "—"),
                    "Unrealised PnL": f"{float(p.get('unrealizedProfit',0)):+,.4f}",
                    "Leverage":  p.get("leverage", "—"),
                } for p in positions]
                st.dataframe(pd.DataFrame(pos_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No open positions.")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — LIVE PRICES
# ═══════════════════════════════════════════════════════════════════════════
with tab_price:
    st.subheader("📊 Live Mark Prices")

    syms = st.multiselect(
        "Symbols to track",
        ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","AVAXUSDT","LTCUSDT"],
        default=["BTCUSDT","ETHUSDT","SOLUSDT"],
    )

    c1, _ = st.columns([1, 3])
    with c1:
        fetch_p = st.button("🔄 Fetch Prices", use_container_width=True, key="btn_price")

    if fetch_p or auto_refresh:
        if not syms:
            st.warning("Select at least one symbol.")
        else:
            prev = st.session_state.get("prev_prices", {})
            curr = {}

            cols = st.columns(min(len(syms), 4))
            for i, sym in enumerate(syms):
                ok, data = api_get(f"/ticker/{sym}")
                with cols[i % len(cols)]:
                    if ok and isinstance(data, dict):
                        p = float(data.get("price", 0))
                        curr[sym] = p
                        delta = round(p - prev[sym], 2) if sym in prev else None
                        st.metric(sym, f"${p:,.2f}",
                                  delta=f"{delta:+.2f}" if delta is not None else None)
                    else:
                        st.metric(sym, "Error")

            st.session_state["prev_prices"] = curr

            if auto_refresh:
                time.sleep(5)
                st.rerun()
    else:
        st.info("Click **Fetch Prices** or enable auto-refresh in the sidebar.")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — OPEN ORDERS
# ═══════════════════════════════════════════════════════════════════════════
with tab_open:
    st.subheader("📋 Open Orders on Testnet")

    c1, c2 = st.columns([2, 1])
    with c1:
        oo_sym = st.text_input("Filter by symbol (blank = all)", placeholder="BTCUSDT",
                               key="oo_sym")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_oo = st.button("🔄 Fetch Open Orders", use_container_width=True,
                             disabled=not server_up, key="btn_oo")

    if not server_up:
        st.warning("Start the API server first.")
    elif fetch_oo:
        params = {"symbol": oo_sym.strip().upper()} if oo_sym.strip() else {}
        with st.spinner("Fetching…"):
            ok, data = api_get("/open-orders", params=params)

        if not ok:
            st.error(f"Error: {data}")
        elif not data:
            st.info("No open orders found.")
        else:
            rows = [{
                "Order ID": o.get("orderId"),
                "Symbol":   o.get("symbol"),
                "Side":     o.get("side"),
                "Type":     o.get("type"),
                "Price":    o.get("price"),
                "Orig Qty": o.get("origQty"),
                "Executed": o.get("executedQty"),
                "Status":   o.get("status"),
                "Time":     pd.to_datetime(o.get("time"), unit="ms")
                             .strftime("%Y-%m-%d %H:%M:%S") if o.get("time") else "—",
            } for o in data]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"{len(rows)} open order(s)")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — ORDER HISTORY (from SQLite via API)
# ═══════════════════════════════════════════════════════════════════════════
with tab_history:
    st.subheader("📜 Executed Order History")
    st.caption("Orders filled by the Execution Engine and persisted to SQLite.")

    c1, _ = st.columns([1, 3])
    with c1:
        fetch_hist = st.button("🔄 Refresh History", use_container_width=True,
                               disabled=not server_up, key="btn_hist")

    if not server_up:
        st.warning("Start the API server first.")
    elif fetch_hist or st.session_state.get("hist_fetched"):
        with st.spinner("Fetching order history from DB…"):
            ok, data = api_get("/orders")

        if not ok:
            st.error(f"Error: {data}")
        elif not data:
            st.info("No orders in database yet. Place an order to see it here.")
        else:
            st.session_state["hist_fetched"] = True
            rows = [{
                "ID":           o.get("id"),
                "Order ID":     o.get("order_id"),
                "Symbol":       o.get("symbol"),
                "Side":         o.get("side"),
                "Type":         o.get("order_type"),
                "Status":       o.get("status"),
                "Orig Qty":     o.get("orig_qty"),
                "Executed Qty": o.get("executed_qty"),
                "Avg Price":    o.get("avg_price"),
                "Limit Price":  o.get("price"),
            } for o in data]
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(rows)} order(s) in history")

            # Summary stats
            if len(rows) > 1:
                st.markdown("---")
                st.markdown("#### Quick Stats")
                s1, s2, s3 = st.columns(3)
                buys  = sum(1 for r in rows if r["Side"] == "BUY")
                sells = sum(1 for r in rows if r["Side"] == "SELL")
                syms_uniq = df["Symbol"].nunique()
                s1.metric("Total Orders", len(rows))
                s2.metric("BUY / SELL", f"{buys} / {sells}")
                s3.metric("Unique Symbols", syms_uniq)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 6 — LOGS
# ═══════════════════════════════════════════════════════════════════════════
with tab_logs:
    st.subheader("📄 Log Viewer")

    from pathlib import Path
    log_path = Path(__file__).parent / "logs" / "trading_bot.json"
    log_plain = Path(__file__).parent / "logs" / "trading_bot.log"

    # Try JSON log first, fallback to plain
    active_log = log_path if log_path.exists() else (log_plain if log_plain.exists() else None)

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        refresh_log = st.button("🔄 Refresh", use_container_width=True, key="btn_log")
    with c2:
        n_lines = st.number_input("Lines", min_value=20, max_value=500, value=80, step=20)
    with c3:
        lvl_filter = st.selectbox("Level filter", ["ALL","INFO","WARNING","ERROR","DEBUG"],
                                  key="lvl_filter")

    if active_log:
        raw_lines = active_log.read_text(encoding="utf-8", errors="replace").splitlines()

        if lvl_filter != "ALL":
            raw_lines = [l for l in raw_lines if lvl_filter in l.upper()]

        display = raw_lines[-n_lines:]

        coloured = []
        for line in display:
            ul = line.upper()
            if "ERROR"   in ul: coloured.append(f"🔴 {line}")
            elif "WARNING" in ul: coloured.append(f"🟡 {line}")
            elif "INFO"    in ul: coloured.append(f"🟢 {line}")
            elif "DEBUG"   in ul: coloured.append(f"⚪ {line}")
            else:                 coloured.append(f"   {line}")

        st.markdown(
            f'<div class="log-box">{"<br>".join(coloured)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"Log: `{active_log.resolve()}` — {len(raw_lines)} matching lines shown"
        )
        st.download_button(
            "⬇️ Download Log",
            data=active_log.read_bytes(),
            file_name=active_log.name,
            mime="text/plain",
        )
    else:
        st.info(
            "No log file found yet.\n\n"
            "Start the server with `python -m bot.cli serve` — "
            "the log file is created on first startup."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<small style='color:#555'>Binance Futures Testnet only — no real funds involved. "
    "Built for Primetrade.ai Python Developer Intern assignment.</small>",
    unsafe_allow_html=True,
)
