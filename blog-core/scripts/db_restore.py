#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import psycopg2

def validate_postgres_db(db_url):
    """Validate PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database validation failed: {e}")
        return False

def restore_database(db_url, backup_path):
    """Restore PostgreSQL database from backup"""
    try:
        # Use psql to restore backup
        os.system(f'psql "{db_url}" < "{backup_path}"')
        
        # Validate the restored database
        if not validate_postgres_db(db_url):
            print("Restore failed: Database validation failed")
            return False
            
        print(f"Database restored from: {backup_path}")
        return True
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python db_restore.py <backup_file>")
        sys.exit(1)

    backup_path = Path(sys.argv[1])
    if not backup_path.exists():
        print(f"Error: Backup file {backup_path} does not exist")
        sys.exit(1)

    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")
    
    # Restore database
    if restore_database(db_url, backup_path):
        print("Restore completed successfully")
        sys.exit(0)
    else:
        print("Restore failed")
        sys.exit(1)
