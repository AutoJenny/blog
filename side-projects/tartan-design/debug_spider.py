#!/usr/bin/env python3
"""
Debug script to examine the HTML structure of tartan register pages
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_az_page():
    """Debug the A-Z page structure"""
    url = "https://www.tartanregister.gov.uk/az?searchString=A"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"Page title: {soup.title.get_text() if soup.title else 'No title'}")
        print(f"Page length: {len(response.content)} bytes")
        
        # Look for any links
        all_links = soup.find_all('a', href=True)
        print(f"Total links found: {len(all_links)}")
        
        # Look for tartan detail links specifically
        tartan_links = []
        for link in all_links:
            href = link['href']
            if 'tartanDetails' in href:
                tartan_links.append((href, link.get_text(strip=True)))
        
        print(f"Tartan detail links found: {len(tartan_links)}")
        
        if tartan_links:
            print("First 5 tartan links:")
            for i, (href, text) in enumerate(tartan_links[:5]):
                print(f"  {i+1}. {text} -> {href}")
        else:
            print("No tartan detail links found. Looking for other patterns...")
            
            # Look for any links with 'ref=' parameter
            ref_links = [link for link in all_links if 'ref=' in link['href']]
            print(f"Links with 'ref=' parameter: {len(ref_links)}")
            
            if ref_links:
                print("First 5 ref links:")
                for i, link in enumerate(ref_links[:5]):
                    print(f"  {i+1}. {link.get_text(strip=True)} -> {link['href']}")
            
            # Look for table structures
            tables = soup.find_all('table')
            print(f"Tables found: {len(tables)}")
            
            # Look for divs with specific classes
            content_divs = soup.find_all('div', class_=re.compile(r'content|main|result'))
            print(f"Content divs found: {len(content_divs)}")
            
            # Print a sample of the HTML to see structure
            print("\nSample HTML (first 1000 chars):")
            print(response.text[:1000])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_az_page()
