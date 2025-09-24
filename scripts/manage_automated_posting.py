#!/usr/bin/env python3
"""
Management script for automated posting system
Provides commands to start, stop, status, and test the automated posting
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_cron_status():
    """Check if the automated posting cron job is active"""
    returncode, stdout, stderr = run_command("crontab -l | grep automated_posting")
    if returncode == 0 and "automated_posting" in stdout:
        return True, stdout.strip()
    return False, "No automated posting cron job found"

def install_cron():
    """Install the automated posting cron job"""
    print("Installing automated posting cron job...")
    
    # Run the setup script
    returncode, stdout, stderr = run_command("/Users/autojenny/Documents/projects/blog/scripts/setup_automated_posting_cron.sh")
    
    if returncode == 0:
        print("✅ Cron job installed successfully")
        print(stdout)
    else:
        print("❌ Failed to install cron job")
        print(f"Error: {stderr}")
    
    return returncode == 0

def remove_cron():
    """Remove the automated posting cron job"""
    print("Removing automated posting cron job...")
    
    # Get current crontab
    returncode, stdout, stderr = run_command("crontab -l")
    if returncode != 0:
        print("❌ Failed to read current crontab")
        return False
    
    # Remove automated posting lines
    lines = stdout.split('\n')
    filtered_lines = [line for line in lines if 'automated_posting' not in line]
    
    # Write back to crontab
    new_crontab = '\n'.join(filtered_lines)
    returncode, stdout, stderr = run_command(f"echo '{new_crontab}' | crontab -")
    
    if returncode == 0:
        print("✅ Cron job removed successfully")
    else:
        print("❌ Failed to remove cron job")
        print(f"Error: {stderr}")
    
    return returncode == 0

def test_posting():
    """Test the automated posting system"""
    print("Testing automated posting system...")
    
    # Run the automated posting script
    returncode, stdout, stderr = run_command("cd /Users/autojenny/Documents/projects/blog && python3 scripts/automated_posting.py")
    
    if returncode == 0:
        print("✅ Test completed successfully")
        print(stdout)
    else:
        print("❌ Test failed")
        print(f"Error: {stderr}")
    
    return returncode == 0

def show_logs():
    """Show recent logs from automated posting"""
    log_file = "/Users/autojenny/Documents/projects/blog/logs/automated_posting.log"
    
    if os.path.exists(log_file):
        print(f"Recent logs from {log_file}:")
        print("-" * 50)
        
        # Show last 20 lines
        returncode, stdout, stderr = run_command(f"tail -20 {log_file}")
        if returncode == 0:
            print(stdout)
        else:
            print("No recent logs found")
    else:
        print("Log file not found. Run a test first to generate logs.")

def show_status():
    """Show status of automated posting system"""
    print("Automated Posting System Status")
    print("=" * 40)
    
    # Check cron job
    is_active, cron_info = check_cron_status()
    if is_active:
        print("✅ Cron job: ACTIVE")
        print(f"   {cron_info}")
    else:
        print("❌ Cron job: NOT ACTIVE")
    
    # Check log file
    log_file = "/Users/autojenny/Documents/projects/blog/logs/automated_posting.log"
    if os.path.exists(log_file):
        print("✅ Log file: EXISTS")
        
        # Get last run time
        returncode, stdout, stderr = run_command(f"tail -1 {log_file}")
        if returncode == 0 and stdout.strip():
            print(f"   Last run: {stdout.strip()}")
    else:
        print("❌ Log file: NOT FOUND")
    
    # Check script permissions
    script_file = "/Users/autojenny/Documents/projects/blog/scripts/automated_posting.py"
    if os.path.exists(script_file):
        print("✅ Script file: EXISTS")
    else:
        print("❌ Script file: NOT FOUND")

def main():
    parser = argparse.ArgumentParser(description="Manage automated posting system")
    parser.add_argument('command', choices=['install', 'remove', 'status', 'test', 'logs'],
                       help='Command to run')
    
    args = parser.parse_args()
    
    if args.command == 'install':
        install_cron()
    elif args.command == 'remove':
        remove_cron()
    elif args.command == 'status':
        show_status()
    elif args.command == 'test':
        test_posting()
    elif args.command == 'logs':
        show_logs()

if __name__ == "__main__":
    main()
