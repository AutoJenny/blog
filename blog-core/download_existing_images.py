#!/usr/bin/env python3
"""
Script to download images for existing JSON response files that don't have local images yet.
"""

import os
import json
import requests
import glob
from datetime import datetime

def download_image_from_json(json_filepath):
    """Download image from JSON response file if it doesn't already have a local image."""
    try:
        # Read the JSON file
        with open(json_filepath, 'r') as f:
            data = json.load(f)
        
        # Check if it already has a local image path
        if 'local_image_path' in data:
            print(f"Already has local image: {data['local_image_path']}")
            return
        
        # Get the image URL
        llm_output = data.get('llm_output', {})
        if not llm_output.get('success') or not llm_output.get('image_url'):
            print(f"No image URL found in {json_filepath}")
            return
        
        image_url = llm_output['image_url']
        base_dir = os.path.dirname(json_filepath)
        
        # Download the image
        print(f"Downloading image from: {image_url}")
        image_response = requests.get(image_url, timeout=60)
        
        if image_response.status_code == 200:
            # Determine image format
            if 'png' in image_url.lower():
                image_ext = 'png'
            elif 'jpg' in image_url.lower() or 'jpeg' in image_url.lower():
                image_ext = 'jpg'
            else:
                image_ext = 'png'
            
            # Create image filename using timestamp from JSON
            timestamp = data.get('timestamp', datetime.now().isoformat())
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0].replace('-', '') + '_' + timestamp.split('T')[1][:6].replace(':', '')
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            image_filename = f"generated_image_{timestamp}.{image_ext}"
            image_filepath = os.path.join(base_dir, image_filename)
            
            # Save the image
            with open(image_filepath, 'wb') as f:
                f.write(image_response.content)
            
            print(f"Generated image stored at: {image_filepath}")
            
            # Update the JSON file with local image path
            data['local_image_path'] = image_filepath
            data['local_image_filename'] = image_filename
            
            with open(json_filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Updated JSON file with local image path")
        else:
            print(f"Failed to download image: HTTP {image_response.status_code}")
            
    except Exception as e:
        print(f"Error processing {json_filepath}: {str(e)}")

def main():
    """Find and process all JSON response files."""
    # Find all JSON response files
    json_files = glob.glob("static/content/posts/*/sections/*/raw/dalle_response_*.json")
    
    print(f"Found {len(json_files)} JSON response files")
    
    for json_file in json_files:
        print(f"\nProcessing: {json_file}")
        download_image_from_json(json_file)

if __name__ == "__main__":
    main() 