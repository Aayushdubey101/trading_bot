import httpx
import hmac
import hashlib
from typing import Dict, Any, Optional
from ..core.config import settings
from ..core.utils import get_timestamp_ms, retry_async

class BinanceAPIError(Exception):
    def __init__(self, status_code: int, code: int, msg: str):
        self.status_code = status_code
        self.code = code
        self.msg = msg
        super().__init__(f"Binance API Error {status_code} [{code}]: {msg}")

class BinanceAsyncClient:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or settings.binance_testnet_api_key
        self.api_secret = api_secret or settings.binance_testnet_api_secret
        self.base_url = settings.binance_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign parameters using HMAC-SHA256."""
        if not self.api_secret:
            raise ValueError("API Secret is required for signing requests")
            
        params['timestamp'] = get_timestamp_ms()
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        return params

    async def _request(self, method: str, endpoint: str, signed: bool = False, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        if signed:
            params = self._sign(params)

        headers = {"X-MBX-APIKEY": self.api_key} if self.api_key else {}

        async def _do_request():
            if method == "GET":
                response = await self._client.get(endpoint, params=params, headers=headers)
            elif method == "POST":
                response = await self._client.post(endpoint, data=params, headers=headers)
            elif method == "DELETE":
                response = await self._client.delete(endpoint, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            try:
                data = response.json()
            except ValueError:
                raise BinanceAPIError(response.status_code, -1, "Invalid JSON response")

            if response.status_code != 200 or ("code" in data and data["code"] < 0):
                raise BinanceAPIError(
                    status_code=response.status_code,
                    code=data.get("code", -1),
                    msg=data.get("msg", "Unknown error")
                )
            return data

        return await retry_async(_do_request)

    async def get_exchange_info(self) -> Dict[str, Any]:
        return await self._request("GET", "/fapi/v1/exchangeInfo")

    async def get_account(self) -> Dict[str, Any]:
        return await self._request("GET", "/fapi/v2/account", signed=True)

    async def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        if price is not None:
            params["price"] = price
            
        params.update(kwargs)
        return await self._request("POST", "/fapi/v1/order", signed=True, params=params)

    async def close(self):
        await self._client.aclose()
