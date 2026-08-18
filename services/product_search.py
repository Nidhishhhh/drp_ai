"""
drp.ai — services/product_search.py
Fires multiple parallel RapidAPI queries for wider product variety.
"""

import httpx
import os
import asyncio

RAPIDAPI_KEY = os.getenv(
    "RAPIDAPI_KEY",
    "API-KEY"
)

RAPIDAPI_HOST = "real-time-product-search.p.rapidapi.com"
RAPIDAPI_URL = "https://real-time-product-search.p.rapidapi.com/search"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

# Multiple query templates per category for variety
CATEGORY_QUERY_SETS = {
    "short_sleeve_top": [
        "{color} {gender} short sleeve t-shirt",
        "{color} {gender} half sleeve top",
        "{color} {gender} casual tee",
    ],
    "long_sleeve_top": [
        "{color} {gender} full sleeve t-shirt",
        "{color} {gender} long sleeve shirt",
        "{color} {gender} full sleeve casual top",
    ],
    "short_sleeve_outwear": [
        "{color} {gender} short sleeve jacket",
        "{color} {gender} half sleeve bomber",
        "{color} {gender} short jacket",
    ],
    "long_sleeve_outwear": [
        "{color} {gender} jacket",
        "{color} {gender} hoodie sweatshirt",
        "{color} {gender} winter coat",
        "{color} {gender} puffer jacket",
        "{color} {gender} windbreaker",
    ],
    "vest": [
        "{color} {gender} vest top",
        "{color} {gender} sleeveless jacket",
        "{color} {gender} waistcoat",
    ],
    "sling": [
        "{color} {gender} sling top",
        "{color} {gender} camisole",
        "{color} {gender} strap top",
    ],
    "shorts": [
        "{color} {gender} shorts",
        "{color} {gender} casual shorts",
        "{color} {gender} bermuda shorts",
    ],
    "trousers": [
        "{color} {gender} trousers",
        "{color} {gender} formal pants",
        "{color} {gender} slim fit pants",
    ],
    "skirt": [
        "{color} skirt",
        "{color} midi skirt",
        "{color} flared skirt",
    ],
    "short_sleeve_dress": [
        "{color} short dress",
        "{color} casual mini dress",
        "{color} summer dress",
    ],
    "long_sleeve_dress": [
        "{color} long sleeve dress",
        "{color} maxi dress",
        "{color} full sleeve dress",
    ],
    "vest_dress": [
        "{color} vest dress",
        "{color} sleeveless dress",
        "{color} pinafore dress",
    ],
    "sling_dress": [
        "{color} sling dress",
        "{color} strap dress",
        "{color} slip dress",
    ],
    "unknown": [
        "{color} {gender} fashion clothing",
        "{color} {gender} casual wear",
    ],
}

GENDER_LABELS = {
    "male":    "men",
    "female":  "women",
    "unknown": "",
}


def build_queries(category: str, color: str, gender: str) -> list[str]:
    templates = CATEGORY_QUERY_SETS.get(category, CATEGORY_QUERY_SETS["unknown"])
    gender_label = GENDER_LABELS.get(gender, "")
    color_label = color if color and color not in ("white", "unknown", "") else ""

    queries = []
    for template in templates:
        q = template.format(color=color_label, gender=gender_label)
        # Clean up extra spaces
        q = " ".join(q.split()).strip()
        queries.append(q)

    return queries


async def fetch_single_query(client: httpx.AsyncClient, query: str, limit: int = 3) -> list:
    params = {
        "q": query,
        "country": "in",
        "language": "en",
        "limit": str(limit * 2),
        "page": "1",
    }

    try:
        response = await client.get(RAPIDAPI_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        products = data.get("data", {}).get("products", [])

        results = []
        for p in products:
            if not isinstance(p, dict):
                continue

            price_str = str(p.get("price", ""))
            buy_link = p.get("product_page_url", "")
            store = p.get("store_name", "Online Store")
            photos = p.get("product_photos", [])
            image = photos[0] if photos else None

            try:
                clean = price_str.replace("₹", "").replace("$", "").replace(",", "").strip()
                clean = clean.split("–")[0].split("-")[0].strip()
                price = float(clean) if clean else None
            except (ValueError, AttributeError):
                price = None

            if not buy_link:
                continue

            results.append({
                "name": p.get("product_title", "Fashion Item"),
                "image": image,
                "price": price,
                "price_display": price_str,
                "currency": "INR" if "₹" in price_str else "USD",
                "store": store,
                "buy_link": buy_link,
                "rating": p.get("product_rating"),
                "source": "rapidapi",
                "query": query,
            })

            if len(results) >= limit:
                break

        return results

    except Exception as e:
        print(f"[drp.ai] RapidAPI query failed '{query}': {e}")
        return []


async def fetch_products(category: str, color: str = "", gender: str = "unknown", limit: int = 10) -> list:
    queries = build_queries(category, color, gender)
    print(f"[drp.ai] Firing {len(queries)} parallel queries for '{category}'")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fetch_single_query(client, q, limit=3) for q in queries]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge and deduplicate by buy_link
    seen_links = set()
    merged = []
    for batch in all_results:
        if isinstance(batch, Exception):
            continue
        for product in batch:
            link = product.get("buy_link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                merged.append(product)

    print(f"[drp.ai] Merged {len(merged)} unique products from {len(queries)} queries")
    return merged[:limit]


async def enrich_results_with_products(similar_items: list, detected_category: str, color: str = "", gender: str = "unknown") -> list:
    products = await fetch_products(detected_category, color=color, gender=gender, limit=10)

    if not products:
        return similar_items

    for i, item in enumerate(similar_items):
        if i < len(products):
            product = products[i]
        else:
            break

        item["metadata"]["buy_link"] = product["buy_link"]
        item["metadata"]["product_name"] = product["name"]
        item["metadata"]["product_image"] = product["image"]
        item["metadata"]["store"] = product["store"]
        if product["price"]:
            item["metadata"]["price"] = product["price"]
            item["metadata"]["currency"] = product["currency"]
        item["metadata"]["price_display"] = product.get("price_display", "")
        item["metadata"]["rating"] = product.get("rating")

    return similar_items
