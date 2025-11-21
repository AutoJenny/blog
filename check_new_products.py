#!/usr/bin/env python3
"""Check for new products since last update"""
import psycopg
import json
import urllib.request
from datetime import datetime

# Get cutoff from stats
cutoff = None
try:
    with urllib.request.urlopen("http://localhost:5000/api/clan/cache/stats", timeout=10) as r:
        data = json.load(r)
        last_updates = data.get("last_updates", {})
        cutoff_str = last_updates.get("products_last_update")
        if cutoff_str:
            # Parse ISO format timestamp
            cutoff = cutoff_str.replace("T", " ").split(".")[0]
        else:
            # Fallback to known last update
            cutoff = "2025-09-16 13:11:43"
except Exception as e:
    print(f"Error fetching stats: {e}")
    cutoff = "2025-09-16 13:11:43"

print(f"Checking for products clan_created_at >= {cutoff}")
print("-" * 80)

# Connect to database
try:
    conn = psycopg.connect(host="localhost", dbname="blog", user="autojenny")
    with conn.cursor() as cur:
        # Count new products (using clan_created_at, fallback to first_seen_at for legacy products)
        cur.execute("""
            SELECT COUNT(*) 
            FROM clan_products 
            WHERE COALESCE(clan_created_at, first_seen_at) >= to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS')
        """, (cutoff,))
        count = cur.fetchone()[0]
        print(f"Total new products since cutoff: {count}")
        
        if count > 0:
            # Get sample of new products
            cur.execute("""
                SELECT id, sku, name, 
                       to_char(COALESCE(clan_created_at, first_seen_at), 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as created_at,
                       to_char(clan_created_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as clan_created,
                       to_char(first_seen_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as first_seen,
                       to_char(last_updated, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as last_upd
                FROM clan_products 
                WHERE COALESCE(clan_created_at, first_seen_at) >= to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS')
                ORDER BY COALESCE(clan_created_at, first_seen_at) DESC
                LIMIT 50
            """, (cutoff,))
            
            print("\nSample of new products (up to 50):")
            print("-" * 80)
            for row in cur.fetchall():
                created_display = row[3] if row[4] else f"{row[5]} (sync discovery)"
                print(f"ID: {row[0]} | SKU: {row[1]} | Name: {row[2][:60]}... | Created: {created_display} | Last updated: {row[6]}")
        else:
            print("\nNo new products found since the cutoff date.")
            
        # Also check current total products
        cur.execute("SELECT COUNT(*) FROM clan_products")
        total = cur.fetchone()[0]
        print(f"\nTotal products in cache: {total}")
        
    conn.close()
    
except Exception as e:
    print(f"Database error: {e}")
    import traceback
    traceback.print_exc()

