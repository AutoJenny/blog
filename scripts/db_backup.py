#!/usr/bin/env python3
import os
import sys
import sqlite3
import shutil
import gzip
from datetime import datetime
import hashlib
from pathlib import Path


def calculate_db_hash(db_path):
    """Calculate SHA-256 hash of database file"""
    sha256_hash = hashlib.sha256()
    with open(db_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_sqlite_db(db_path):
    """Validate SQLite database integrity"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        return result == "ok"
    except Exception as e:
        print(f"Error validating database: {e}")
        return False


def compress_file(source_path, dest_path):
    """Compress a file using gzip"""
    with open(source_path, "rb") as f_in:
        with gzip.open(dest_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    return dest_path


def decompress_file(source_path, dest_path):
    """Decompress a gzip file"""
    with gzip.open(source_path, "rb") as f_in:
        with open(dest_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    return dest_path


def create_backup(source_db, backup_dir, max_backups=10):
    """Create a validated backup of the database with rotation"""
    if not os.path.exists(source_db):
        print(f"Error: Source database {source_db} does not exist")
        return False

    # Create backup directory if it doesn't exist
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"blog_db_{timestamp}.db"
    compressed_path = backup_dir / f"blog_db_{timestamp}.db.gz"

    try:
        # Create initial backup
        shutil.copy2(source_db, backup_path)

        # Validate backup
        if not validate_sqlite_db(backup_path):
            print("Error: Backup validation failed")
            os.remove(backup_path)
            return False

        # Compare hashes
        original_hash = calculate_db_hash(source_db)
        backup_hash = calculate_db_hash(backup_path)
        if original_hash != backup_hash:
            print("Error: Backup hash mismatch")
            os.remove(backup_path)
            return False

        # Compress the backup
        compress_file(backup_path, compressed_path)
        os.remove(backup_path)  # Remove uncompressed version

        # Create hash file for compressed backup
        with open(f"{compressed_path}.sha256", "w") as f:
            f.write(backup_hash)

        # Rotate old backups
        backups = sorted(backup_dir.glob("blog_db_*.db.gz"))
        if len(backups) > max_backups:
            for old_backup in backups[:-max_backups]:
                os.remove(old_backup)
                hash_file = Path(f"{old_backup}.sha256")
                if hash_file.exists():
                    hash_file.unlink()

        print(f"Backup created successfully: {compressed_path}")
        return True

    except Exception as e:
        print(f"Error creating backup: {e}")
        if backup_path.exists():
            backup_path.unlink()
        if compressed_path.exists():
            compressed_path.unlink()
        return False


def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    source_db = project_root / "instance" / "blog.db"

    # Store backups in user's home directory to survive project changes
    backup_dir = Path.home() / ".blog_backups"

    if create_backup(source_db, backup_dir):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
