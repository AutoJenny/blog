#!/usr/bin/env python3
import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from db_backup import validate_sqlite_db, calculate_db_hash

print("This script is deprecated. Please use PostgreSQL monitoring tools instead.")
sys.exit(0)


def check_database_health(db_path):
    """Perform comprehensive database health check"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "database": str(db_path),
        "checks": {},
    }

    try:
        # Check if file exists and is readable
        if not db_path.exists():
            results["checks"]["exists"] = False
            return results

        results["checks"]["exists"] = True
        results["checks"]["size"] = db_path.stat().st_size

        # Check file permissions
        results["checks"]["permissions"] = oct(db_path.stat().st_mode)[-3:]

        # Validate database integrity
        results["checks"]["integrity"] = validate_sqlite_db(db_path)

        # Calculate and verify hash
        current_hash = calculate_db_hash(db_path)
        results["checks"]["hash"] = current_hash

        # Check table structure
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get table list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        results["checks"]["tables"] = len(tables)

        # Check row counts
        table_stats = {}
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            table_stats[table_name] = count
        results["checks"]["table_stats"] = table_stats

        # Check for fragmentation
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        cursor.execute("PRAGMA freelist_count")
        freelist_count = cursor.fetchone()[0]

        fragmentation = (freelist_count / page_count) * 100 if page_count > 0 else 0
        results["checks"]["fragmentation"] = f"{fragmentation:.1f}%"

        conn.close()

    except Exception as e:
        results["error"] = str(e)

    return results


def save_health_check(results, output_dir):
    """Save health check results to a JSON file"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.fromisoformat(results["timestamp"]).strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"health_check_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return output_file


def alert_if_needed(results):
    """Check results and alert if there are issues"""
    alerts = []

    if not results["checks"].get("exists", False):
        alerts.append("Database file missing")

    if not results["checks"].get("integrity", False):
        alerts.append("Database integrity check failed")

    fragmentation = float(results["checks"].get("fragmentation", "0").rstrip("%"))
    if fragmentation > 20:
        alerts.append(f"High fragmentation: {fragmentation}%")

    if "error" in results:
        alerts.append(f"Error during health check: {results['error']}")

    if alerts:
        print("⚠️ Database Health Alerts:")
        for alert in alerts:
            print(f"  - {alert}")
        return False

    print("✅ Database health check passed")
    return True


def main():
    project_root = Path(__file__).parent.parent
    db_path = project_root / "instance" / "blog.db"
    health_dir = Path.home() / ".blog_backups" / "health_checks"

    results = check_database_health(db_path)
    output_file = save_health_check(results, health_dir)

    print(f"\nHealth check results saved to: {output_file}")
    if not alert_if_needed(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
