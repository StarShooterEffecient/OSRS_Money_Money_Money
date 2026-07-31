#!/usr/bin/env python3
"""
OmniFlip Engine v2.0 - Quantitative OSRS Grand Exchange Trading Framework
Fully autonomous execution via GitHub Actions.
"""

import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
USER_AGENT = "OmniFlipEngine/2.0 (GitHub OpenSource Engine; contact: @MrOmniMasta)"
API_MAPPING = "https://prices.runescape.wiki/api/v1/osrs/mapping"
API_LATEST = "https://prices.runescape.wiki/api/v1/osrs/latest"
API_5M = "https://prices.runescape.wiki/api/v1/osrs/5m"
API_1H = "https://prices.runescape.wiki/api/v1/osrs/1h"

DB_FILE = "omniflip_memory.db"
OUTPUT_JSON = "public/data.json"

TAX_RATE = 0.02  # 2% GE Tax
MAX_TAX = 5_000_000  # Capped at 5M GP per item

# Discord Webhook Environment Variable
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# High-Volume Potions for Decanting Arbitrage
POTION_FAMILIES = [
    "Saradomin brew",
    "Super restore",
    "Prayer potion",
    "Super combat potion",
    "Divine super combat potion",
    "Ranging potion",
    "Extended super antifire",
    "Stamina potion",
    "Super attack",
    "Super strength",
    "Super defence",
    "Bastion potion",
    "Battlemage potion"
]

# ==========================================
# DATABASE & PERSISTENT MEMORY LAYER
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Historical price & volume telemetry
    cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
            timestamp TEXT,
            item_id INTEGER,
            high_price INTEGER,
            low_price INTEGER,
            volume_5m INTEGER,
            vms_score REAL,
            PRIMARY KEY(timestamp, item_id)
        )''')
    
    # Self-refining confidence weights & performance logs
    cursor.execute('''CREATE TABLE IF NOT EXISTS item_confidence (
            item_id INTEGER PRIMARY KEY,
            confidence_weight REAL DEFAULT 1.0,
            successful_flips INTEGER DEFAULT 0,
            failed_flips INTEGER DEFAULT 0,
            last_updated TEXT
        )''')
    
    conn.commit()
    return conn

def get_item_confidence_weights(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, confidence_weight FROM item_confidence")
    return {row[0]: row[1] for row in cursor.fetchall()}

def update_confidence_weight(conn, item_id, adjustment_factor):
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    cursor.execute('''INSERT INTO item_confidence (item_id, confidence_weight, last_updated)
        VALUES (?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET
            confidence_weight = MIN(MAX(confidence_weight * ?, 0.20), 2.50),
            last_updated = ?''', (item_id, 1.0 * adjustment_factor, now_str, adjustment_factor, now_str))
    conn.commit()

# ==========================================
# API TELEMETRY FETCHING
# ==========================================
def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"[ERROR] Failed fetching {url}: {e}", file=sys.stderr)
        return {}

# ==========================================
# MATHEMATICAL & TACTICAL ENGINES
# ==========================================
def calculate_ge_tax(price: int) -> int:
    """Calculates 2% GE tax with 5M cap (items under 100 GP exempt)."""
    if price < 100:
        return 0
    tax = math.floor(price * TAX_RATE)
    return min(tax, MAX_TAX)

def apply_behavioral_pricing(price: int, mode: str) -> int:
    """
    Behavioral Front-Running Engine: Beats psychological anchor points.
    Applies asymmetric offset to bypass round-number human order queues.
    """
    if price <= 0:
        return price

    anchors = [1_000_000, 500_000, 100_000, 50_000, 10_000]
    
    for anchor in anchors:
        if abs(price - anchor) <= (anchor * 0.01):
            if mode == "buy":
                return anchor + 13
            elif mode == "sell":
                return anchor - 17

    if mode == "buy":
        return price + 1
    else:
        return max(1, price - 1)

def evaluate_flips(mappings, latest_data, data_5m, data_1h, confidence_weights):
    opportunities = []
    latest = latest_data.get('data', {})
    v5m = data_5m.get('data', {})
    v1h = data_1h.get('data', {})

    for item in mappings:
        item_id = item['id']
        str_id = str(item_id)
        name = item['name']
        limit = item.get('limit', 10000)
        members = item.get('members', True)
        high_alch = item.get('highalch', 0)

        if str_id not in latest or str_id not in v5m:
            continue

        high_price = latest[str_id].get('high')
        low_price = latest[str_id].get('low')

        if not high_price or not low_price or low_price >= high_price or low_price <= 0:
            continue

        vol_5m = v5m[str_id].get('highPriceVolume', 0) + v5m[str_id].get('lowPriceVolume', 0)
        vol_1h = v1h.get(str_id, {}).get('highPriceVolume', 0) + v1h.get(str_id, {}).get('lowPriceVolume', 0) if str_id in v1h else vol_5m * 12
        hourly_vol_est = max(vol_5m * 12, vol_1h)

        tax = calculate_ge_tax(high_price)
        net_sell = high_price - tax
        net_margin = net_sell - low_price
        roi = (net_margin / low_price) * 100 if low_price > 0 else 0

        if net_margin <= 100:
            continue

        effective_limit = limit if limit else 10000
        cap_constrained_volume = min(hourly_vol_est, effective_limit)
        
        w_item = confidence_weights.get(item_id, 1.0)
        vms_score = net_margin * cap_constrained_volume * w_item

        nature_rune_price = 90
        alch_floor = high_alch - nature_rune_price if high_alch > 0 else 0

        rec_buy = apply_behavioral_pricing(low_price, "buy")
        rec_sell = apply_behavioral_pricing(high_price, "sell")

        opportunities.append({
            'id': item_id,
            'name': name,
            'members': members,
            'low_price': low_price,
            'high_price': high_price,
            'tax': tax,
            'net_margin': net_margin,
            'roi_pct': round(roi, 2),
            'buy_limit': effective_limit,
            'hourly_volume': cap_constrained_volume,
            'vms_score': round(vms_score, 0),
            'confidence_weight': round(w_item, 2),
            'high_alch': high_alch,
            'alch_floor': alch_floor,
            'action_buy_at': rec_buy,
            'action_sell_at': rec_sell
        })

    opportunities.sort(key=lambda x: x['vms_score'], reverse=True)
    return opportunities

def evaluate_decanting_arbitrage(mappings, latest_data):
    latest = latest_data.get('data', {})
    mapping_dict = {item['name']: item for item in mappings}
    
    arbitrage_opportunities = []

    for base_name in POTION_FAMILIES:
        name_1d = f"{base_name}(1)"
        name_4d = f"{base_name}(4)"

        if name_1d in mapping_dict and name_4d in mapping_dict:
            item_1d = mapping_dict[name_1d]
            item_4d = mapping_dict[name_4d]

            str_1d = str(item_1d['id'])
            str_4d = str(item_4d['id'])

            if str_1d in latest and str_4d in latest:
                buy_1d_low = latest[str_1d].get('low')
                sell_4d_high = latest[str_4d].get('high')

                if buy_1d_low and sell_4d_high:
                    cost_for_4d = buy_1d_low * 4
                    tax = calculate_ge_tax(sell_4d_high)
                    net_revenue = sell_4d_high - tax
                    profit_per_potion = net_revenue - cost_for_4d
                    roi = (profit_per_potion / cost_for_4d) * 100 if cost_for_4d > 0 else 0

                    if profit_per_potion > 200:
                        arbitrage_opportunities.append({
                            'potion': base_name,
                            'buy_1d_price': buy_1d_low,
                            'cost_4d_equiv': cost_for_4d,
                            'sell_4d_price': sell_4d_high,
                            'tax': tax,
                            'profit_per_combine': profit_per_potion,
                            'roi_pct': round(roi, 2),
                            'buy_limit_4d': item_4d.get('limit', 2000)
                        })

    arbitrage_opportunities.sort(key=lambda x: x['profit_per_combine'], reverse=True)
    return arbitrage_opportunities

def detect_panic_snipes(opportunities):
    snipes = [o for o in opportunities if o['roi_pct'] >= 8.0 and o['net_margin'] >= 2500 and o['hourly_volume'] >= 10]
    snipes.sort(key=lambda x: x['roi_pct'], reverse=True)
    return snipes[:15]

def dispatch_discord_alert(top_flips, panic_snipes, decant_arbs):
    if not DISCORD_WEBHOOK_URL:
        return

    embeds = []
    
    if top_flips:
        tf = top_flips[0]
        embeds.append({
            "title": "🚨 HIGH-CONVICTION FLIP SIGNAL",
            "color": 15844367,
            "fields": [
                {"name": "Item", "value": f"**{tf['name']}**", "inline": True},
                {"name": "Buy At", "value": f"{tf['action_buy_at']:,} GP", "inline": True},
                {"name": "Sell At", "value": f"{tf['action_sell_at']:,} GP", "inline": True},
                {"name": "Net Margin", "value": f"+{tf['net_margin']:,} GP ({tf['roi_pct']}%)", "inline": True},
                {"name": "VMS Score", "value": f"{tf['vms_score']:,}", "inline": True},
                {"name": "Hourly Vol", "value": f"{tf['hourly_volume']:,}", "inline": True}
            ]
        })

    if panic_snipes:
        ps = panic_snipes[0]
        embeds.append({
            "title": "⚡ CAPITULATION PANIC SNIPE DETECTED",
            "color": 15158332,
            "fields": [
                {"name": "Item", "value": f"**{ps['name']}**", "inline": True},
                {"name": "Low Price", "value": f"{ps['low_price']:,} GP", "inline": True},
                {"name": "ROI Potential", "value": f"**{ps['roi_pct']}%**", "inline": True},
                {"name": "Target Sell", "value": f"{ps['action_sell_at']:,} GP", "inline": True}
            ]
        })

    payload = {
        "username": "OmniFlip Intelligence",
        "content": "📡 **OmniFlip Market Engine Dispatch**",
        "embeds": embeds
    }

    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': USER_AGENT}
        )
        with urllib.request.urlopen(req) as resp:
            print(f"[WEBHOOK] Alert dispatched successfully. Response code: {resp.status}")
    except Exception as e:
        print(f"[ERROR] Failed dispatching Discord alert: {e}", file=sys.stderr)

def main():
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.isoformat()
    print(f"[{now_str}] Executing OmniFlip Quantitative Market Engine...")

    conn = init_db()
    confidence_weights = get_item_confidence_weights(conn)

    mappings = fetch_json(API_MAPPING)
    latest = fetch_json(API_LATEST)
    data_5m = fetch_json(API_5M)
    data_1h = fetch_json(API_1H)

    if not mappings or not latest:
        print("[CRITICAL] Failed to retrieve mandatory API feeds. Aborting execution.")
        sys.exit(1)

    opportunities = evaluate_flips(mappings, latest, data_5m, data_1h, confidence_weights)
    decant_arbs = evaluate_decanting_arbitrage(mappings, latest)
    panic_snipes = detect_panic_snipes(opportunities)

    cursor = conn.cursor()
    for opp in opportunities[:100]:
        cursor.execute('''INSERT OR REPLACE INTO price_history (timestamp, item_id, high_price, low_price, volume_5m, vms_score)
            VALUES (?, ?, ?, ?, ?, ?)''', (now_str, opp['id'], opp['high_price'], opp['low_price'], opp['hourly_volume'], opp['vms_score']))
    conn.commit()
    conn.close()

    os.makedirs("public", exist_ok=True)
    payload_output = {
        "updated_at": now_str,
        "summary": {
            "total_items_analyzed": len(mappings),
            "profitable_flips_found": len(opportunities),
            "decant_arbitrages_found": len(decant_arbs),
            "panic_snipes_found": len(panic_snipes)
        },
        "top_flips": opportunities[:50],
        "decant_arbitrage": decant_arbs[:20],
        "panic_snipes": panic_snipes
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(payload_output, f, indent=2)

    print(f"[{now_str}] Output successfully written to {OUTPUT_JSON}.")
    print(f"Evaluated {len(opportunities)} profitable opportunities and {len(decant_arbs)} potion decant margins.")

    dispatch_discord_alert(opportunities[:5], panic_snipes[:5], decant_arbs[:5])

if __name__ == "__main__":
    main()
