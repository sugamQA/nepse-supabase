"""
NEPSE Daily Price → Supabase
Fetches today's prices from NEPSE and upserts into Supabase.
Credentials are read from environment variables (set as GitHub Secrets).
"""

import os
import sys
import requests
import urllib3
from datetime import date
from supabase import create_client, Client

# NEPSE uses a certificate not in standard CA bundles — suppress the warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Credentials from environment (GitHub Secrets) ────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TABLE_NAME   = "nepse_daily_prices"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: SUPABASE_URL and SUPABASE_KEY must be set as environment variables.")
    sys.exit(1)

# ── NEPSE public API ──────────────────────────────────────────────────────────
NEPSE_API_URL = "https://www.nepalstock.com.np/api/nots/market/export/todays-price/58"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NEPSE-Fetcher/1.0)",
    "Accept": "application/json",
    "Referer": "https://www.nepalstock.com.np/",
}

# ── Field mapping: NEPSE API key → Supabase column ───────────────────────────
COLUMN_MAP = {
    "businessDate":           "business_date",
    "securityId":             "security_id",
    "symbol":                 "symbol",
    "securityName":           "security_name",
    "openPrice":              "open_price",
    "highPrice":              "high_price",
    "lowPrice":               "low_price",
    "closePrice":             "close_price",
    "totalTradedQuantity":    "total_traded_quantity",
    "totalTradedValue":       "total_traded_value",
    "previousDayClosePrice":  "previous_day_close_price",
    "fiftyTwoWeekHigh":       "fifty_two_week_high",
    "fiftyTwoWeekLow":        "fifty_two_week_low",
    "lastUpdatedTime":        "last_updated_time",
    "lastUpdatedPrice":       "last_updated_price",
    "totalTrades":            "total_trades",
    "averageTradedPrice":     "average_traded_price",
    "marketCapitalization":   "market_capitalization",
}


def fetch_nepse_prices() -> list[dict]:
    print(f"📡 Fetching NEPSE prices for {date.today()}...")
    resp = requests.get(NEPSE_API_URL, headers=HEADERS, timeout=30, verify=False)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("content", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError(f"Unexpected response format: {type(data)}")
    print(f"✅ Fetched {len(items)} records")
    return items


def transform(raw: list[dict]) -> list[dict]:
    return [{db_col: item.get(api_key) for api_key, db_col in COLUMN_MAP.items()} for item in raw]


def upsert(rows: list[dict]) -> None:
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"📤 Upserting {len(rows)} rows into '{TABLE_NAME}'...")
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        client.table(TABLE_NAME).upsert(batch, on_conflict="business_date,symbol").execute()
        print(f"   ✔ Batch {i // batch_size + 1}: {len(batch)} rows saved")
    print(f"✅ Done! {len(rows)} rows upserted.")


def main():
    print("=" * 50)
    print("  NEPSE Daily Price Sync  ")
    print("=" * 50)
    raw  = fetch_nepse_prices()
    rows = transform(raw)
    upsert(rows)
    print("\n🎉 All done!")


if __name__ == "__main__":
    main()
