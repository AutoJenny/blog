#!/usr/bin/env python3
"""Test the complete header image flow for post 82"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publish.header_image_finder import get_header_image
from publish.post_data_loader import load_post_data, prepare_post_for_publication
from clan_publisher import ClanPublisher
from publish.post_data_loader import load_sections

post_id = 82

print("=" * 80)
print("TESTING HEADER IMAGE FLOW FOR POST 82")
print("=" * 80)

# Step 1: Get header image
print("\n1. GET_HEADER_IMAGE")
header_image = get_header_image(post_id)
if header_image:
    print(f"   ✅ Found: {header_image.get('path')}")
else:
    print("   ❌ NOT FOUND")
    sys.exit(1)

# Step 2: Load post and prepare
print("\n2. PREPARE_POST_FOR_PUBLICATION")
post = load_post_data(post_id)
post = prepare_post_for_publication(post, header_image)
if post.get('header_image'):
    print(f"   ✅ Post has header_image: {post['header_image'].get('path')}")
else:
    print("   ❌ Post missing header_image")
    sys.exit(1)

# Step 3: Process images
print("\n3. PROCESS_IMAGES")
publisher = ClanPublisher()
sections = load_sections(post_id)
uploaded_images = publisher.process_images(post, sections)

header_path = post['header_image']['path']
print(f"   Header path in post: {repr(header_path)}")
print(f"   Uploaded images keys: {list(uploaded_images.keys())}")

if header_path in uploaded_images:
    print(f"   ✅ Header image uploaded: {uploaded_images[header_path]}")
else:
    print(f"   ❌ Header path NOT in uploaded_images!")
    print(f"   Looking for: {repr(header_path)}")
    for key in uploaded_images.keys():
        if 'header' in key.lower():
            print(f"   Similar key found: {repr(key)}")
    sys.exit(1)

# Step 4: Check create_or_update_post
print("\n4. CREATE_OR_UPDATE_POST would use:")
print(f"   header_image_path: {header_path}")
print(f"   uploaded_url: {uploaded_images[header_path]}")
print(f"   ✅ Ready to publish!")

