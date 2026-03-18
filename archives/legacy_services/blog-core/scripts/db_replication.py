#!/usr/bin/env python3
import os
import time
import psycopg2
from datetime import datetime

class DatabaseReplicator:
    def __init__(self, source_url, replica_url):
        self.source_url = source_url
        self.replica_url = replica_url
        self.last_sync = None

    def validate_connection(self, db_url):
        """Validate PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Database validation failed for {db_url}: {e}")
            return False

    def replicate(self):
        """Replicate source database to replica"""
        if not self.validate_connection(self.source_url):
            print("Source database validation failed")
            return False

        try:
            # Use pg_dump and psql to replicate
            dump_cmd = f'pg_dump "{self.source_url}" | psql "{self.replica_url}"'
            result = os.system(dump_cmd)
            
            if result == 0:
                self.last_sync = datetime.now()
                print(f"Replication completed at {self.last_sync}")
                return True
            else:
                print("Replication failed")
                return False

        except Exception as e:
            print(f"Replication error: {e}")
            return False

    def monitor(self, interval=300):  # 5 minutes
        """Monitor and replicate periodically"""
        print(f"Starting replication monitor (interval: {interval}s)")
        
        while True:
            print("\nChecking databases...")
            
            if self.replicate():
                print("Waiting for next sync...")
            else:
                print("Replication failed, will retry...")
            
            time.sleep(interval)

if __name__ == "__main__":
    # Get database URLs from environment
    source_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")
    replica_url = os.getenv("REPLICA_URL", "postgresql://postgres:postgres@localhost:5432/blog_replica")
    
    replicator = DatabaseReplicator(source_url, replica_url)
    
    try:
        replicator.monitor()
    except KeyboardInterrupt:
        print("\nReplication monitor stopped")
