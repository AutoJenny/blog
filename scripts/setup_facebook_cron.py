#!/usr/bin/env python3
"""
Setup Facebook Token Refresh Cron Job
Creates a cron job to automatically refresh Facebook tokens monthly.
"""

import os
import subprocess
import sys

def setup_cron_job():
    """Set up cron job for Facebook token refresh."""
    try:
        # Get the current directory
        current_dir = os.getcwd()
        script_path = os.path.join(current_dir, 'scripts', 'facebook_perpetual_tokens.py')
        
        # Create the cron job entry
        cron_entry = f"0 2 1 * * cd {current_dir} && PYTHONPATH={current_dir} python3 {script_path} >> logs/facebook_cron.log 2>&1"
        
        print("Setting up Facebook token refresh cron job...")
        print(f"Cron entry: {cron_entry}")
        
        # Add to crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing_crontab = result.stdout
        
        # Check if our job already exists
        if 'facebook_perpetual_tokens.py' in existing_crontab:
            print("✅ Facebook token refresh cron job already exists")
            return True
        
        # Add our job to existing crontab
        new_crontab = existing_crontab + f"\n# Facebook token refresh (monthly)\n{cron_entry}\n"
        
        # Write new crontab
        result = subprocess.run(['crontab', '-'], input=new_crontab, text=True, capture_output=True)
        
        if result.returncode == 0:
            print("✅ Facebook token refresh cron job added successfully")
            print("   - Runs monthly on the 1st at 2:00 AM")
            print("   - Logs to logs/facebook_cron.log")
            return True
        else:
            print(f"❌ Failed to add cron job: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

def create_log_directory():
    """Create logs directory if it doesn't exist."""
    try:
        os.makedirs('logs', exist_ok=True)
        print("✅ Logs directory ready")
        return True
    except Exception as e:
        print(f"❌ Failed to create logs directory: {e}")
        return False

if __name__ == "__main__":
    print("Setting up Facebook perpetual token system...")
    
    # Create logs directory
    if not create_log_directory():
        sys.exit(1)
    
    # Setup cron job
    if setup_cron_job():
        print("\n✅ Facebook perpetual token system setup completed!")
        print("\nNext steps:")
        print("1. Get a fresh user access token from Facebook")
        print("2. Update the user_access_token in the database")
        print("3. The system will automatically refresh tokens monthly")
    else:
        print("\n❌ Setup failed")
        sys.exit(1)
