#!/usr/bin/env python3
"""
Debug script to test tartan name extraction
"""

import requests
from bs4 import BeautifulSoup
import re

def test_tartan_name_extraction():
    """Test tartan name extraction from a specific page"""
    url = "https://www.tartanregister.gov.uk/tartanDetails.aspx?ref=10053"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        content_text = soup.get_text()
        
        print("Testing different tartan name extraction methods:")
        
        # Method 1: From page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            print(f"1. Page title: {title_text}")
            if title_text.startswith('Tartan Details - '):
                tartan_name = title_text.replace('Tartan Details - ', '').strip()
                print(f"   Extracted from title: {tartan_name}")
        
        # Method 2: From content text
        tartan_name_match = re.search(r'Tartan Details - ([^\n]+)', content_text)
        if tartan_name_match:
            tartan_name = tartan_name_match.group(1).strip()
            print(f"2. From content regex: {tartan_name}")
        
        # Method 3: Look for the actual tartan name in the content
        # The tartan name appears in the content as "A J Gallacher"
        lines = content_text.split('\n')
        for i, line in enumerate(lines):
            if 'Tartan Details -' in line:
                print(f"3. Found 'Tartan Details -' in line {i}: {line.strip()}")
                # Look at the next few lines
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('The information'):
                        print(f"   Next line {j}: {next_line}")
                        break
        
        # Method 4: Look for the tartan name in quotes
        quote_match = re.search(r'"([^"]+)" tartan', content_text)
        if quote_match:
            print(f"4. From quotes: {quote_match.group(1)}")
        
        # Method 5: Look for the breadcrumb or navigation
        breadcrumb_match = re.search(r'you are in:\s*\n\s*([^\n]+)', content_text)
        if breadcrumb_match:
            print(f"5. From breadcrumb: {breadcrumb_match.group(1).strip()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tartan_name_extraction()

