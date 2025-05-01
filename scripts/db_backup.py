#!/usr/bin/env python3
import os
import shutil
import hashlib
from datetime import datetime, timedelta
import psycopg2
from pathlib import Path


def calculate_db_hash(db_path):
    """Calculate SHA-256 hash of database file"""
    sha256_hash = hashlib.sha256()
    with open(db_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_postgres_db(db_url):
    """Validate PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            # Database doesn't exist, create it
            db_name = db_url.split("/")[-1]
            base_url = "/".join(db_url.split("/")[:-1])
            try:
                conn = psycopg2.connect(base_url + "/postgres")
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(f'CREATE DATABASE {db_name}')
                cur.close()
                conn.close()
                print(f"Created database {db_name}")
                return True
            except Exception as create_error:
                print(f"Failed to create database: {create_error}")
                return False
        print(f"Database validation failed: {e}")
        return False
    except Exception as e:
        print(f"Database validation failed: {e}")
        return False


def rotate_backups(backup_dir, max_backups=10):
    """Keep only the most recent backups"""
    backup_files = sorted(Path(backup_dir).glob("blog_backup_*.sql"))
    while len(backup_files) >= max_backups:
        oldest = backup_files.pop(0)
        try:
            oldest.unlink()
            print(f"Removed old backup: {oldest}")
        except Exception as e:
            print(f"Failed to remove old backup {oldest}: {e}")


def backup_database(db_url, backup_dir="backups"):
    """Create a backup of the PostgreSQL database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(backup_dir) / f"blog_backup_{timestamp}.sql"
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # Use pg_dump to create backup
        result = os.system(f'pg_dump "{db_url}" > "{backup_path}"')
        
        if result != 0 or not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
            print("Backup failed: Backup file was not created or is empty")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return None
            
        print(f"Backup created at: {backup_path}")
        
        # Rotate old backups
        rotate_backups(backup_dir)
        
        return backup_path
    except Exception as e:
        print(f"Backup failed: {e}")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return None


if __name__ == "__main__":
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")
    
    # Validate database
    if not validate_postgres_db(db_url):
        print("Database validation failed")
        exit(1)
    
    # Create backup
    backup_path = backup_database(db_url)
    if not backup_path:
        print("Backup failed")
        exit(1)
    
    print("Backup completed successfully")
