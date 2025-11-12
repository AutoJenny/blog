#!/usr/bin/env python3
"""
Run the image to images table migration.
Executes the SQL migration script and shows results.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.unified_config import get_config

def run_migration():
    """Run the migration script."""
    config = get_config()
    db_url = config.DATABASE_URL
    
    # Parse database URL
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
                return False
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
                return False
    else:
        print("❌ Invalid database URL format")
        return False
    
    migration_file = project_root / 'migrations' / 'migrate_image_to_images.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print("=" * 80)
    print("IMAGE TO IMAGES TABLE MIGRATION")
    print("=" * 80)
    print(f"Database: {db_name}")
    print(f"Host: {db_host}:{db_port}")
    print(f"User: {db_user}")
    print(f"Migration file: {migration_file}")
    print()
    print("⚠️  IMPORTANT: This will modify the database!")
    print("   Make sure you have a backup before proceeding.")
    print()
    
    # Read migration script and uncomment COMMIT
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Replace the commented COMMIT with active COMMIT
    migration_sql = migration_sql.replace('-- COMMIT;', 'COMMIT;')
    migration_sql = migration_sql.replace('-- ROLLBACK;', '-- ROLLBACK;  -- (commented out)')
    
    # Create temp file with active COMMIT
    temp_file = project_root / 'migrations' / 'migrate_image_to_images_temp.sql'
    with open(temp_file, 'w') as f:
        f.write(migration_sql)
    
    try:
        # Run migration
        cmd = ['psql', '-h', db_host, '-U', db_user, '-d', db_name, '-f', str(temp_file)]
        
        if db_port and db_port != '5432':
            cmd.extend(['-p', db_port])
        
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password
        
        print("Running migration...")
        print("-" * 80)
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
        
        # Show output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("-" * 80)
            print("✅ Migration completed successfully!")
            return True
        else:
            print("-" * 80)
            print(f"❌ Migration failed with return code {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("❌ psql not found. Please install PostgreSQL client tools.")
        if temp_file.exists():
            temp_file.unlink()
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)



