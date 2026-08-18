"""
drp.ai — services/currency.py
Fetches live USD to INR exchange rate from ExchangeRate-API.
Caches the rate for 1 hour to minimize API calls.
Free tier: 1,500 requests/month — with caching effectively 36,000 searches/month.
"""

import httpx
import os
import time

EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "API-KEY")
EXCHANGE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/USD/INR"

# Cache
_cached_rate: float = 84.0  # fallback default
_cache_time: float = 0
_cache_ttl: int = 3600  # 1 hour


async def get_usd_to_inr() -> float:
    """
    Returns current USD to INR exchange rate.
    Cached for 1 hour to save API calls.
    """
    global _cached_rate, _cache_time

    now = time.time()
    if now - _cache_time < _cache_ttl:
        return _cached_rate

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(EXCHANGE_URL)
            response.raise_for_status()
            data = response.json()

        rate = data.get("conversion_rate")
        if rate and isinstance(rate, (int, float)):
            _cached_rate = float(rate)
            _cache_time = now
            print(f"[drp.ai] Exchange rate updated: 1 USD = ₹{_cached_rate:.2f}")
        else:
            print(f"[drp.ai] Exchange rate fetch failed — using cached: ₹{_cached_rate:.2f}")

    except Exception as e:
        print(f"[drp.ai] Exchange rate error: {e} — using cached: ₹{_cached_rate:.2f}")

    return _cached_rate


def convert_usd_to_inr(usd_price: float, rate: float) -> tuple[float, str]:
    """
    Converts USD price to INR.
    Returns (price_float, formatted_display_string).
    """
    inr = round(usd_price * rate)
    display = f"₹{inr:,}"
    return float(inr), display
