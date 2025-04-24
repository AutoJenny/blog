#!/usr/bin/env python3
import os
import sys
import time
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
import sqlite3
from threading import Thread, Event
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/replication.log")],
)


class DatabaseReplicator:
    def __init__(self, primary_path, replica_path, check_interval=60):
        self.primary_path = Path(primary_path)
        self.replica_path = Path(replica_path)
        self.check_interval = check_interval
        self.stop_event = Event()
        self.status = {
            "last_sync": None,
            "status": "initializing",
            "primary_hash": None,
            "replica_hash": None,
            "error": None,
        }
        self._save_status()

    def _calculate_hash(self, db_path):
        """Calculate SHA-256 hash of database file"""
        if not db_path.exists():
            return None

        hasher = hashlib.sha256()
        with open(db_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _save_status(self):
        """Save replication status to a file"""
        status_file = self.primary_path.parent / "replication_status.json"
        with open(status_file, "w") as f:
            json.dump(self.status, f, indent=2, default=str)

    def _validate_replica(self):
        """Validate replica database integrity"""
        try:
            conn = sqlite3.connect(self.replica_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            return result == "ok"
        except Exception as e:
            logging.error(f"Replica validation failed: {e}")
            return False

    def _sync_databases(self):
        """Synchronize primary and replica databases"""
        try:
            # Check if primary exists
            if not self.primary_path.exists():
                raise FileNotFoundError("Primary database not found")

            # Create replica directory if needed
            self.replica_path.parent.mkdir(parents=True, exist_ok=True)

            # Calculate primary hash
            primary_hash = self._calculate_hash(self.primary_path)
            replica_hash = self._calculate_hash(self.replica_path)

            # Check if sync is needed
            if primary_hash != replica_hash:
                # Create a temporary copy
                temp_replica = self.replica_path.with_suffix(".tmp")
                shutil.copy2(self.primary_path, temp_replica)

                # Validate temporary copy
                conn = sqlite3.connect(temp_replica)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                if cursor.fetchone()[0] != "ok":
                    conn.close()
                    temp_replica.unlink()
                    raise Exception("Integrity check failed on temporary replica")
                conn.close()

                # Replace replica with temporary copy
                if self.replica_path.exists():
                    self.replica_path.unlink()
                temp_replica.rename(self.replica_path)

                # Update status
                self.status.update(
                    {
                        "last_sync": datetime.now(),
                        "status": "synchronized",
                        "primary_hash": primary_hash,
                        "replica_hash": self._calculate_hash(self.replica_path),
                        "error": None,
                    }
                )
                logging.info("Database synchronized successfully")
            else:
                self.status.update(
                    {
                        "status": "in sync",
                        "primary_hash": primary_hash,
                        "replica_hash": replica_hash,
                        "error": None,
                    }
                )
                logging.info("Databases already in sync")

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            self.status.update({"status": "error", "error": error_msg})
            logging.error(error_msg)

        self._save_status()

    def start(self):
        """Start replication monitoring"""

        def monitor():
            while not self.stop_event.is_set():
                self._sync_databases()
                self.stop_event.wait(self.check_interval)

        self.monitor_thread = Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        logging.info("Replication monitoring started")

    def stop(self):
        """Stop replication monitoring"""
        self.stop_event.set()
        self.monitor_thread.join()
        logging.info("Replication monitoring stopped")

    def get_status(self):
        """Get current replication status"""
        return self.status


def main():
    # Get database paths
    project_root = Path(__file__).parent.parent
    primary_db = project_root / "instance" / "blog.db"
    replica_db = project_root / "instance" / "blog.replica.db"

    # Create replicator
    replicator = DatabaseReplicator(primary_db, replica_db)

    try:
        # Start replication
        replicator.start()

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping replication...")
        replicator.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
