#!/usr/bin/env python3
"""
Create database backup before migration.
Uses pg_dump via subprocess.
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.unified_config import get_config

def create_backup():
    """Create a database backup using pg_dump."""
    config = get_config()
    
    # Get database URL
    db_url = config.DATABASE_URL
    
    # Parse database URL to get components
    # Format: postgresql://user:password@host:port/dbname
    if db_url.startswith('postgresql://'):
        parts = db_url.replace('postgresql://', '').split('@')
        if len(parts) == 2:
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            if len(host_db) == 2:
                db_name = host_db[1]
                host_port = host_db[0].split(':')
                db_host = host_port[0]
                db_port = host_port[1] if len(host_port) > 1 else '5432'
                db_user = user_pass[0]
                db_password = user_pass[1] if len(user_pass) > 1 else ''
            else:
                print("❌ Could not parse database URL")
                return None
        else:
            # Try simpler format
            parts = db_url.replace('postgresql://', '').split('/')
            if len(parts) == 2:
                db_name = parts[1]
                host_user = parts[0].split('@')
                if len(host_user) == 2:
                    db_user = host_user[0]
                    host_port = host_user[1].split(':')
                    db_host = host_port[0]
                    db_port = host_port[1] if len(host_port) > 1 else '5432'
                else:
                    db_user = os.getenv('PGUSER', 'postgres')
                    host_port = parts[0].split(':')
                    db_host = host_port[0]
                    db_port = host_port[1] if len(host_port) > 1 else '5432'
            else:
                print("❌ Could not parse database URL")
                return None
    else:
        print("❌ Invalid database URL format")
        return None
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = project_root / 'backups'
    backup_dir.mkdir(exist_ok=True)
    backup_file = backup_dir / f'blog_backup_pre_migration_{timestamp}.sql'
    
    print("=" * 80)
    print("DATABASE BACKUP - PRE MIGRATION")
    print("=" * 80)
    print(f"Database: {db_name}")
    print(f"Host: {db_host}:{db_port}")
    print(f"User: {db_user}")
    print(f"Backup file: {backup_file}")
    print()
    
    # Create backup command
    cmd = [
        'pg_dump',
        '-h', db_host,
        '-U', db_user,
        '-d', db_name,
        '--no-owner',
        '--no-privileges',
        '-f', str(backup_file)
    ]
    
    # Add port if specified
    if db_port and db_port != '5432':
        cmd.extend(['-p', db_port])
    
    # Set password in environment if provided
    env = os.environ.copy()
    if db_password:
        env['PGPASSWORD'] = db_password
    
    try:
        print("Creating backup...")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = backup_file.stat().st_size
            print(f"✅ Backup created successfully!")
            print(f"   File: {backup_file}")
            print(f"   Size: {file_size / 1024 / 1024:.2f} MB")
            return str(backup_file)
        else:
            print(f"❌ Backup failed!")
            print(f"   Error: {result.stderr}")
            if backup_file.exists():
                backup_file.unlink()
            return None
            
    except FileNotFoundError:
        print("❌ pg_dump not found. Please install PostgreSQL client tools.")
        return None
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        if backup_file.exists():
            backup_file.unlink()
        return None

if __name__ == "__main__":
    backup_path = create_backup()
    if backup_path:
        print()
        print("=" * 80)
        print("✅ BACKUP COMPLETE - Safe to proceed with migration")
        print("=" * 80)
        sys.exit(0)
    else:
        print()
        print("=" * 80)
        print("❌ BACKUP FAILED - Do not proceed with migration")
        print("=" * 80)
        sys.exit(1)




