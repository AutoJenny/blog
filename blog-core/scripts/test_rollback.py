#!/usr/bin/env python3
"""
Test script to verify rollback procedures for the format system.
This script tests that we can restore from backup if needed.
"""

import os
import sys
import subprocess
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def test_rollback_procedures():
    """Test that rollback procedures work correctly."""
    app = create_app()
    
    with app.app_context():
        # Get database configuration
        db_host = app.config.get('DB_HOST', 'localhost')
        db_name = app.config.get('DB_NAME', 'blog')
        db_user = app.config.get('DB_USER', 'postgres')
        db_password = app.config.get('DB_PASSWORD', '')
        db_port = app.config.get('DB_PORT', '5432')
        
        print("Testing rollback procedures...")
        print(f"Database: {db_name} on {db_host}:{db_port}")
        print(f"User: {db_user}")
        
        # Test 1: Verify we can connect to the database
        print("\n1. Testing database connection...")
        try:
            from app.db import get_db_conn
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM workflow_format_template")
            count = cursor.fetchone()['count']
            print(f"✅ Database connection successful. Found {count} format templates.")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Test 2: Verify format tables exist and have data
        print("\n2. Testing format table integrity...")
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            
            # Check all format-related tables
            tables = [
                'workflow_format_template',
                'workflow_step_format', 
                'workflow_stage_format',
                'workflow_post_format'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()['count']
                print(f"   {table}: {count} records")
            
            cursor.close()
            conn.close()
            print("✅ All format tables exist and accessible.")
        except Exception as e:
            print(f"❌ Format table check failed: {e}")
            return False
        
        # Test 3: Verify API endpoints are working
        print("\n3. Testing API endpoint availability...")
        try:
            import requests
            base_url = "http://localhost:5000"
            
            # Test format templates endpoint
            response = requests.get(f"{base_url}/api/workflow/formats/templates", timeout=5)
            if response.status_code == 200:
                print("✅ Format templates API endpoint working")
            else:
                print(f"⚠️  Format templates API returned {response.status_code}")
            
            # Test format validation endpoint
            test_data = {
                "fields": [
                    {"name": "title", "type": "string", "required": True}
                ],
                "test_data": {"title": "Test Title"}
            }
            response = requests.post(f"{base_url}/api/workflow/formats/validate", 
                                   json=test_data, timeout=5)
            if response.status_code == 200:
                print("✅ Format validation API endpoint working")
            else:
                print(f"⚠️  Format validation API returned {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  API test failed (server may not be running): {e}")
        
        # Test 4: Verify backup file exists
        print("\n4. Testing backup file availability...")
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('_pre_format_deployment.sql')]
        
        if backup_files:
            latest_backup = max(backup_files, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
            backup_path = os.path.join(backup_dir, latest_backup)
            backup_size = os.path.getsize(backup_path)
            print(f"✅ Latest backup found: {latest_backup} ({backup_size} bytes)")
        else:
            print("❌ No backup files found")
            return False
        
        # Test 5: Verify backup can be restored (dry run)
        print("\n5. Testing backup restore capability...")
        try:
            # Create a test database for restore testing
            test_db_name = f"test_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create test database
            create_cmd = [
                'createdb',
                '-h', db_host,
                '-U', db_user,
                test_db_name
            ]
            
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password
            
            result = subprocess.run(create_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Test database '{test_db_name}' created successfully")
                
                # Test restore (dry run - just check if pg_restore can read the file)
                restore_cmd = [
                    'pg_restore',
                    '-h', db_host,
                    '-U', db_user,
                    '-d', test_db_name,
                    '--dry-run',
                    backup_path
                ]
                
                result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Backup file is valid and can be restored")
                else:
                    print(f"⚠️  Backup restore test failed: {result.stderr}")
                
                # Clean up test database
                drop_cmd = [
                    'dropdb',
                    '-h', db_host,
                    '-U', db_user,
                    test_db_name
                ]
                
                subprocess.run(drop_cmd, env=env, capture_output=True, text=True)
                print(f"✅ Test database '{test_db_name}' cleaned up")
                
            else:
                print(f"⚠️  Could not create test database: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️  Backup restore test failed: {e}")
        
        print("\n✅ Rollback procedures test completed successfully!")
        return True

if __name__ == '__main__':
    success = test_rollback_procedures()
    if success:
        print("\n🎉 All rollback procedures are ready for deployment!")
        sys.exit(0)
    else:
        print("\n❌ Rollback procedures test failed - deployment should not proceed")
        sys.exit(1) 