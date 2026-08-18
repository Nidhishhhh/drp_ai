import httpx
import os
import asyncio
from services.currency import get_usd_to_inr, convert_usd_to_inr

# Your two RapidAPI keys
RAPIDAPI_KEY = os.getenv(
    "RAPIDAPI_KEY",
    "API-KEY"
)

RAPIDAPI_KEY2 = os.getenv(
    "RAPIDAPI_KEY2",
    "API-KEY"
)

LENS_URL = "URL"
LENS_HOST = "real-time-lens-data.p.rapidapi.com"


async def lens_visual_search(image_url: str, limit: int = 10) -> list:
    if not image_url:
        return []

    # 1. Primary Key logic with retries
    primary_keys = [RAPIDAPI_KEY, RAPIDAPI_KEY2]
    last_error = None

    for key_index, api_key in enumerate(primary_keys):
        key_name = f"Key {key_index + 1}"  # Just for logging
        max_retries = 2  # Try each key twice before moving to the next
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Get live exchange rate
                usd_to_inr = await get_usd_to_inr()

                headers = {
                    "x-rapidapi-key": api_key,
                    "x-rapidapi-host": LENS_HOST,
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        LENS_URL,
                        headers=headers,
                        params={
                            "url": image_url,
                            "language": "en",
                            "country": "in",
                        }
                    )

                    # If we get a 429 (rate limit) or 403 (forbidden) we skip to the next key immediately
                    if response.status_code in [429, 403]:
                        print(f"[drp.ai] {key_name} hit rate limit or forbidden (Status {response.status_code}). Switching keys...")
                        raise httpx.HTTPStatusError(
                            f"Rate limit hit on {key_name}",
                            request=response.request,
                            response=response
                        )

                    response.raise_for_status()
                    data = response.json()

                raw_data = data.get("data", [])
                if isinstance(raw_data, list):
                    matches = raw_data
                elif isinstance(raw_data, dict):
                    matches = (
                        raw_data.get("visual_matches") or
                        raw_data.get("matches") or
                        []
                    )
                else:
                    matches = []

                print(f"[drp.ai] {key_name}: {len(matches)} visual matches found")
                
                # --- Standard processing from here onwards ---
                results = []
                seen_links = set()

                for m in matches:
                    if not isinstance(m, dict):
                        continue

                    title = m.get("title") or m.get("name") or "Fashion Item"
                    link = m.get("link") or m.get("url") or m.get("product_url") or ""
                    thumbnail = m.get("thumbnail") or m.get("image") or ""
                    source = m.get("source") or m.get("store") or "Online Store"
                    raw_price = m.get("price")

                    if not link or link in seen_links:
                        continue
                    seen_links.add(link)

                    price = None
                    price_display = ""
                    price_str = ""

                    if raw_price:
                        price_str = str(raw_price)
                        try:
                            if "₹" in price_str:
                                # Already INR
                                clean = price_str.replace("₹", "").replace(",", "").strip()
                                clean = clean.split("–")[0].split("-")[0].strip()
                                price = float(clean)
                                price_display = f"₹{int(price):,}"
                            else:
                                # USD — convert to INR
                                clean = price_str.replace("$", "").replace(",", "").strip()
                                clean = clean.split("–")[0].split("-")[0].strip()
                                if clean:
                                    usd = float(clean)
                                    price, price_display = convert_usd_to_inr(usd, usd_to_inr)
                        except (ValueError, AttributeError):
                            pass

                    if not price_display:
                        price_display = "Check on site"

                    results.append({
                        "name": title,
                        "image": thumbnail,
                        "price": price,
                        "price_display": price_display,
                        "currency": "INR",
                        "store": source,
                        "buy_link": link,
                        "source": "lens",
                    })

                    if len(results) >= limit:
                        break

                INDIAN_DOMAINS = [
                    "myntra.com", "amazon.in", "flipkart.com", "ajio.com",
                    "meesho.com", "nykaa.com", "snapdeal.com", "tatacliq.com",
                    "shopsy.in", "limeroad.com", "bewakoof.com",
                    "thesouledstore.com", "snitch.co.in", "virgio.com",
                    "fashor.com", "libas.in"
                ]

                # Sort: Indian results first, rest after
                indian_results = [
                    r for r in results
                    if any(domain in r.get("buy_link", "").lower() for domain in INDIAN_DOMAINS)
                ]
                other_results = [
                    r for r in results
                    if not any(domain in r.get("buy_link", "").lower() for domain in INDIAN_DOMAINS)
                ]

                final_results = indian_results + other_results
                print(f"[drp.ai] {key_name}: {len(indian_results)} Indian first, {len(other_results)} global after")
                return final_results[:limit]

            except httpx.HTTPStatusError as e:
                last_error = e
                # For 429 or 403, we break out of retries for this key and move to the next key immediately
                if e.response.status_code in [429, 403]:
                    print(f"[drp.ai] {key_name} failed due to rate limiting/forbidden (Status {e.response.status_code}). Switching to next key.")
                    break
                
                # For other HTTP errors (500, 404, etc.), retry attempt
                print(f"[drp.ai] {key_name} HTTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[drp.ai] {key_name} max retries reached. Switching to next key.")

            except Exception as e:
                last_error = e
                print(f"[drp.ai] {key_name} general error (attempt {attempt + 1}/{max_retries}): {e}")
                import traceback
                traceback.print_exc()
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[drp.ai] {key_name} max retries reached. Switching to next key.")

    # --- If BOTH keys have been exhausted ---
    print("[drp.ai] Both RapidAPI keys have been exhausted. Falling back to text search.")
    return []


async def enrich_results_with_visual_search(
    similar_items: list,
    crop_image_url: str,
    detected_category: str,
    color: str = "",
    gender: str = "unknown",
) -> list:
    # Lens visual search — primary
    products = await lens_visual_search(crop_image_url, limit=10)

    # Fallback to text search if Lens returns nothing (after trying both keys)
    if not products:
        print("[drp.ai] Lens returned nothing after trying both keys — falling back to text search")
        from services.product_search import fetch_products
        products = await fetch_products(detected_category, color=color, gender=gender, limit=10)

    print(f"[drp.ai] Total products for enrichment: {len(products)}")

    for i, item in enumerate(similar_items):
        if i < len(products):
            product = products[i]
        else:
            break

        item["metadata"]["buy_link"] = product["buy_link"]
        item["metadata"]["product_name"] = product["name"]
        item["metadata"]["product_image"] = product["image"]
        item["metadata"]["store"] = product["store"]
        item["metadata"]["source"] = product["source"]
        if product.get("price"):
            item["metadata"]["price"] = product["price"]
            item["metadata"]["currency"] = "INR"
        item["metadata"]["price_display"] = product.get("price_display", "")
        item["metadata"]["rating"] = product.get("rating")

    return similar_items
