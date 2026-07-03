"""
drp.ai — Phase 7
Adds realistic dummy prices to metadata.json based on clothing category.

Run this ONCE locally — rewrites metadata.json in place.
Prices are seeded by item_id so they're consistent across runs
(same item always gets the same price).

Replace with real AWIN/CJ affiliate prices after approval.
"""

import json
import random
from pathlib import Path

META_PATH = Path("data/index/metadata.json")
BACKUP_PATH = Path("data/index/metadata_pre_prices.json.bak")

# Realistic price ranges per category (USD)
CATEGORY_PRICE_RANGES = {
    "short_sleeve_top":      (12, 60),
    "long_sleeve_top":       (15, 75),
    "short_sleeve_outwear":  (35, 150),
    "long_sleeve_outwear":   (45, 220),
    "vest":                  (20, 90),
    "sling":                 (15, 65),
    "shorts":                (18, 80),
    "trousers":              (25, 120),
    "skirt":                 (20, 95),
    "short_sleeve_dress":    (25, 130),
    "long_sleeve_dress":     (35, 180),
    "vest_dress":            (25, 110),
    "sling_dress":           (20, 100),
    "unknown":               (20, 100),  # fallback
}

# Dummy store names per category feel
STORES = ["ASOS", "H&M", "Zara", "Mango", "Topshop", "Urban Outfitters", "Uniqlo", "& Other Stories"]


def generate_price(item_id: str, category: str) -> float:
    """Generate a consistent price for an item using item_id as seed."""
    low, high = CATEGORY_PRICE_RANGES.get(category, (20, 100))
    rng = random.Random(int(item_id) if item_id.isdigit() else hash(item_id))
    # Generate a price that ends in .99 or .00 for realism
    base = rng.uniform(low, high)
    rounded = round(base * 2) / 2  # round to nearest 0.50
    return round(rounded - 0.01, 2) if rounded > 1 else round(rounded, 2)


def generate_store(item_id: str) -> str:
    """Pick a consistent store for an item."""
    rng = random.Random(int(item_id) if item_id.isdigit() else hash(item_id))
    return rng.choice(STORES)


def add_prices():
    if not META_PATH.exists():
        print(f"[drp.ai] ERROR: {META_PATH} not found")
        return

    import shutil
    shutil.copy2(META_PATH, BACKUP_PATH)
    print(f"[drp.ai] Backup saved to {BACKUP_PATH}")

    with open(META_PATH, "r") as f:
        metadata = json.load(f)

    total = len(metadata)
    updated = already_has_price = 0

    for item_id, item in metadata.items():
        if "price" in item:
            already_has_price += 1
            continue

        category = item.get("category", "unknown").replace(" ", "_").lower()
        item["price"] = generate_price(item_id, category)
        item["currency"] = "USD"
        item["store"] = generate_store(item_id)
        item["buy_link"] = ""  # populated after AWIN approval
        updated += 1

    with open(META_PATH, "w") as f:
        json.dump(metadata, f)

    print(f"""
[drp.ai] Prices added ✅
  Total items      : {total}
  Updated          : {updated}
  Already had price: {already_has_price}

Sample prices by category:
""")

    # Print one sample per category
    seen = set()
    for item_id, item in metadata.items():
        cat = item.get("category", "unknown")
        if cat not in seen:
            print(f"  {cat:30s} ${item['price']:.2f}  ({item['store']})")
            seen.add(cat)
        if len(seen) >= 13:
            break


if __name__ == "__main__":
    add_prices()