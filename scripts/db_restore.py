#!/usr/bin/env python3
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from db_backup import validate_sqlite_db, calculate_db_hash

print("This script is deprecated. Please use PostgreSQL restore tools instead.")
sys.exit(0)


def list_backups(backup_dir):
    """List all available backups with their timestamps"""
    backup_dir = Path(backup_dir)
    backups = sorted(backup_dir.glob("blog_db_*.db"))

    if not backups:
        print("No backups found")
        return []

    print("\nAvailable backups:")
    for i, backup in enumerate(backups, 1):
        timestamp = backup.stem.replace("blog_db_", "")
        size = backup.stat().st_size / 1024  # Size in KB
        hash_file = Path(str(backup) + ".sha256")
        hash_status = "✓" if hash_file.exists() else "!"

        print(f"{i}. {timestamp} ({size:.1f}KB) [{hash_status}]")

    return backups


def verify_backup(backup_path):
    """Verify backup integrity and hash"""
    if not validate_sqlite_db(backup_path):
        print("Error: Backup failed integrity check")
        return False

    hash_file = Path(str(backup_path) + ".sha256")
    if hash_file.exists():
        with open(hash_file) as f:
            stored_hash = f.read().strip()
        current_hash = calculate_db_hash(backup_path)
        if stored_hash != current_hash:
            print("Error: Backup hash mismatch")
            return False

    return True


def restore_backup(backup_path, target_path):
    """Restore a backup file to the target location"""
    if not verify_backup(backup_path):
        return False

    try:
        # Create a backup of current database if it exists
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_restore_backup = target_path.parent / f"pre_restore_{timestamp}.db"
            shutil.copy2(target_path, pre_restore_backup)
            print(f"Created pre-restore backup: {pre_restore_backup}")

        # Restore the backup
        shutil.copy2(backup_path, target_path)

        # Verify restored database
        if not validate_sqlite_db(target_path):
            print("Error: Restored database failed integrity check")
            if pre_restore_backup.exists():
                shutil.copy2(pre_restore_backup, target_path)
                print("Rolled back to previous version")
            return False

        print(f"Successfully restored database from {backup_path}")
        return True

    except Exception as e:
        print(f"Error during restore: {e}")
        return False


def main():
    backup_dir = Path.home() / ".blog_backups"
    project_root = Path(__file__).parent.parent
    target_db = project_root / "instance" / "blog.db"

    backups = list_backups(backup_dir)
    if not backups:
        sys.exit(1)

    try:
        choice = input("\nEnter backup number to restore (or 'q' to quit): ")
        if choice.lower() == "q":
            sys.exit(0)

        idx = int(choice) - 1
        if 0 <= idx < len(backups):
            if restore_backup(backups[idx], target_db):
                sys.exit(0)
        else:
            print("Invalid backup number")
    except ValueError:
        print("Invalid input")
    except KeyboardInterrupt:
        print("\nRestore cancelled")

    sys.exit(1)


if __name__ == "__main__":
    main()
