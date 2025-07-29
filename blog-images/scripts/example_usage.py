#!/usr/bin/env python3
"""
Example usage of the image processing script
"""

import subprocess
import sys
import os

def run_image_processing(dry_run=True, base_path=None, watermark_path=None):
    """Run the image processing script with given parameters."""
    
    # Build the command
    cmd = [
        sys.executable,  # Use current Python interpreter
        "process_images.py"
    ]
    
    # Add optional parameters
    if dry_run:
        cmd.append("--dry-run")
    
    if base_path:
        cmd.extend(["--base-path", base_path])
    
    if watermark_path:
        cmd.extend(["--watermark-path", watermark_path])
    
    # Run the command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✅ Script executed successfully!")
            print(result.stdout)
        else:
            print("❌ Script failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except Exception as e:
        print(f"❌ Error running script: {str(e)}")

if __name__ == "__main__":
    print("=== Image Processing Script Examples ===\n")
    
    # Example 1: Dry run (recommended first)
    print("Example 1: Dry Run (see what would be processed)")
    print("-" * 50)
    run_image_processing(dry_run=True)
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Actual processing
    print("Example 2: Actual Processing (modifies files)")
    print("-" * 50)
    print("⚠️  WARNING: This will modify your image files!")
    print("Uncomment the line below to run actual processing:")
    # run_image_processing(dry_run=False)
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Custom paths
    print("Example 3: Custom Paths")
    print("-" * 50)
    print("To use custom paths, uncomment and modify:")
    # run_image_processing(
    #     dry_run=True,
    #     base_path="/custom/path/to/content",
    #     watermark_path="/custom/path/to/watermark.png"
    # )
    
    print("\n" + "="*60 + "\n")
    
    print("📋 Usage Instructions:")
    print("1. First run with --dry-run to see what would be processed")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run without --dry-run to actually process images")
    print("4. Processed images will have '_processed' suffix")