#!/usr/bin/env python3
"""
Archive Photo-harvesting JSON data files.
Moves all selected_*.json and photo_search_results*.json files to archive.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def archive_photo_harvesting_data():
    """Archive all Photo-harvesting JSON files."""
    archive_dir = Path("ARCHIVED_PHOTO_HARVESTING/data")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    static_dir = Path("static/content/posts")
    if not static_dir.exists():
        print(f"Static directory not found: {static_dir}")
        return 0
    
    archived_count = 0
    archived_files = []
    
    # Find all Photo-harvesting JSON files
    patterns = [
        "**/selected_landscape.json",
        "**/selected_portrait.json",
        "**/photo_search_results*.json"
    ]
    
    print("Searching for Photo-harvesting JSON files...")
    
    for pattern in patterns:
        for json_file in static_dir.glob(pattern):
            # Create archive path preserving structure
            relative_path = json_file.relative_to(static_dir)
            archive_path = archive_dir / relative_path
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(json_file, archive_path)
            archived_count += 1
            archived_files.append(str(json_file))
            print(f"  Archived: {json_file}")
    
    # Create manifest
    manifest = {
        'archived_at': datetime.now().isoformat(),
        'total_files': archived_count,
        'files': archived_files
    }
    
    manifest_path = archive_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✅ Archived {archived_count} Photo-harvesting JSON files")
    print(f"   Manifest: {manifest_path}")
    
    return archived_count

if __name__ == '__main__':
    archive_photo_harvesting_data()

