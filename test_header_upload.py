#!/usr/bin/env python3
"""Test script to diagnose header image upload issue"""

import sys
import os
sys.path.insert(0, 'blog-launchpad')

from publish.post_data_loader import prepare_post_data
from config.paths import path_resolver
from blog_launchpad.clan_publisher import ClanPublisher

post_id = 90

print("=== FULL DIAGNOSTIC: HEADER vs SECTION IMAGE UPLOAD ===\n")

# Load post data
post, sections = prepare_post_data(post_id)

# Initialize publisher
publisher = ClanPublisher()

# Get header image path
header_path = None
if post.get('header_image'):
    header_path = post['header_image'].get('path')
    print(f"1. HEADER IMAGE PATH:")
    print(f"   From post: {repr(header_path)}")
    print(f"   Type: {type(header_path)}")
    print(f"   Length: {len(header_path) if header_path else 0}")
    
    if header_path:
        fs_path = path_resolver.convert_web_path_to_filesystem(header_path)
        print(f"   Filesystem path: {fs_path}")
        print(f"   File exists: {os.path.exists(fs_path)}")
        if os.path.exists(fs_path):
            print(f"   File size: {os.path.getsize(fs_path)} bytes")
    print()

# Get first section image for comparison
section_path = None
if sections and sections[0].get('image'):
    section_path = sections[0]['image'].get('path')
    print(f"2. SECTION IMAGE PATH (first section):")
    print(f"   From section: {repr(section_path)}")
    print(f"   Type: {type(section_path)}")
    print(f"   Length: {len(section_path) if section_path else 0}")
    
    if section_path:
        fs_path = path_resolver.convert_web_path_to_filesystem(section_path)
        print(f"   Filesystem path: {fs_path}")
        print(f"   File exists: {os.path.exists(fs_path)}")
        if os.path.exists(fs_path):
            print(f"   File size: {os.path.getsize(fs_path)} bytes")
    print()

# Simulate process_images logic
print("3. SIMULATING process_images() LOGIC:\n")

uploaded_images = {}

# Header image processing (as in process_images)
if header_path:
    print(f"   HEADER: Processing header image...")
    fs_path = path_resolver.convert_web_path_to_filesystem(header_path)
    if os.path.exists(fs_path):
        print(f"   ✅ File exists, would call upload_image({repr(fs_path)}, 'header_90_...')")
        print(f"   Would store as: uploaded_images[{repr(header_path)}] = uploaded_url")
        # Don't actually upload, just show what would happen
    else:
        print(f"   ❌ File does not exist!")
    print()

# Section image processing (as in process_images)
if section_path:
    print(f"   SECTION: Processing section image...")
    fs_path = path_resolver.convert_web_path_to_filesystem(section_path)
    if os.path.exists(fs_path):
        print(f"   ✅ File exists, would call upload_image({repr(fs_path)}, 'section_90_1_...')")
        print(f"   Would store as: uploaded_images[{repr(section_path)}] = uploaded_url")
    else:
        print(f"   ❌ File does not exist!")
    print()

# Check path matching in create_or_update_post
print("4. PATH MATCHING IN create_or_update_post():\n")
print(f"   Header path from post: {repr(header_path)}")
print(f"   Would look for key in uploaded_images: {repr(header_path)}")
print(f"   Match check: header_path in uploaded_images = {header_path in uploaded_images if header_path else False}")
print()

print("5. CONCLUSION:")
print("   Both header and section images follow identical processing logic.")
print("   The issue must be either:")
print("   a) Header image upload is failing silently")
print("   b) Path mismatch between stored key and lookup key")
print("   c) Exception being caught and not logged properly")

