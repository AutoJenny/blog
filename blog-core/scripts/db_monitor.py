#!/usr/bin/env python3
import os
import json
import psycopg2
from datetime import datetime

def get_db_stats(db_url):
    """Get PostgreSQL database statistics"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "stats": {}
    }

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Check database size
        cur.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database())),
                   pg_database_size(current_database())
        """)
        pretty_size, size_bytes = cur.fetchone()
        results["stats"]["size"] = {
            "pretty": pretty_size,
            "bytes": size_bytes
        }

        # Get table statistics
        cur.execute("""
            SELECT schemaname, tablename, n_live_tup, n_dead_tup,
                   pg_size_pretty(pg_total_relation_size('"' || schemaname || '"."' || tablename || '"'))
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
        """)
        tables = []
        for schema, table, live_rows, dead_rows, size in cur.fetchall():
            tables.append({
                "schema": schema,
                "name": table,
                "live_rows": live_rows,
                "dead_rows": dead_rows,
                "size": size
            })
        results["stats"]["tables"] = tables

        # Check database health
        cur.execute("SELECT 1")
        results["checks"]["connection"] = True
        results["checks"]["health"] = "ok"

        cur.close()
        conn.close()

    except Exception as e:
        results["checks"]["error"] = str(e)
        results["checks"]["health"] = "error"

    return results

if __name__ == "__main__":
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")
    
    # Get database statistics
    stats = get_db_stats(db_url)
    
    # Print results
    print(json.dumps(stats, indent=2))
