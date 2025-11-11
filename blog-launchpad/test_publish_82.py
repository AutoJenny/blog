#!/usr/bin/env python3
"""Test publication for post 82 with detailed logging"""

import sys
import os
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publish.publish_orchestrator import publish_post_to_clan
from publish.post_data_loader import load_post_data, prepare_post_for_publication
from publish.header_image_finder import get_header_image
from clan_publisher import ClanPublisher

print("=" * 80)
print("TESTING PUBLICATION FOR POST 82")
print("=" * 80)

# Step 1: Check header image finding
print("\n1. GET_HEADER_IMAGE")
header_image = get_header_image(82)
print(f"   Result: {header_image}")
if header_image:
    print(f"   Path: {repr(header_image.get('path'))}")

# Step 2: Check post data loading
print("\n2. LOAD_POST_DATA")
post = load_post_data(82)
print(f"   Post ID: {post.get('id')}")
print(f"   Header image in post: {post.get('header_image')}")

# Step 3: Prepare post
print("\n3. PREPARE_POST_FOR_PUBLICATION")
post = prepare_post_for_publication(post, header_image)
print(f"   Header image after prep: {post.get('header_image')}")
if post.get('header_image'):
    print(f"   Path: {repr(post['header_image'].get('path'))}")

# Step 4: Test process_images
print("\n4. PROCESS_IMAGES")
publisher = ClanPublisher()
from publish.post_data_loader import load_sections
sections = load_sections(82)
uploaded_images = publisher.process_images(post, sections)
print(f"   Uploaded images keys: {list(uploaded_images.keys())}")
for key, value in uploaded_images.items():
    print(f"     '{key}' -> {value}")

# Step 5: Check what create_or_update_post sees
print("\n5. CREATE_OR_UPDATE_POST INPUT")
print(f"   post['header_image']: {post.get('header_image')}")
if post.get('header_image'):
    print(f"   post['header_image']['path']: {repr(post['header_image'].get('path'))}")
print(f"   uploaded_images keys: {list(uploaded_images.keys())}")

# Step 6: Full publication
print("\n6. FULL PUBLICATION")
result = publish_post_to_clan(82)
print(f"   Success: {result.get('success')}")
print(f"   Error: {result.get('error')}")
print(f"   Clan URL: {result.get('clan_url')}")





