#!/usr/bin/env python3
"""
Database backup script for the blog application.
Creates a timestamped backup before major deployments.
"""

import os
import sys
import subprocess
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def create_backup():
    """Create a database backup using pg_dump."""
    app = create_app()
    
    with app.app_context():
        # Get database configuration with fallbacks
        db_host = app.config.get('DB_HOST', 'localhost')
        db_name = app.config.get('DB_NAME', 'blog')
        db_user = app.config.get('DB_USER', 'postgres')
        db_password = app.config.get('DB_PASSWORD', '')
        db_port = app.config.get('DB_PORT', '5432')
        
        # Validate required configuration
        if not db_name:
            print("❌ DB_NAME not configured")
            return None
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        backup_file = os.path.join(backup_dir, f'blog_backup_{timestamp}_pre_format_deployment.sql')
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup command
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '--no-owner',
            '--no-privileges',
            '--clean',
            '--if-exists',
            '-f', backup_file
        ]
        
        # Add port if specified
        if db_port and db_port != '5432':
            cmd.extend(['-p', db_port])
        
        print(f"Creating backup: {backup_file}")
        print(f"Database: {db_name} on {db_host}:{db_port}")
        print(f"User: {db_user}")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            # Set environment variable for password if needed
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Backup created successfully: {backup_file}")
                print(f"Backup size: {os.path.getsize(backup_file)} bytes")
                return backup_file
            else:
                print(f"❌ Backup failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Backup failed with exception: {e}")
            return None

if __name__ == '__main__':
    backup_file = create_backup()
    if backup_file:
        print(f"Backup ready for deployment: {backup_file}")
        sys.exit(0)
    else:
        print("Backup failed - deployment should not proceed")
        sys.exit(1) 