#!/usr/bin/env python3
"""
Debug script to examine tartan detail page structure
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_tartan_detail():
    """Debug a tartan detail page"""
    url = "https://www.tartanregister.gov.uk/tartanDetails.aspx?ref=10053"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"Page title: {soup.title.get_text() if soup.title else 'No title'}")
        
        # Look for the main content
        content_text = soup.get_text()
        
        print("\nLooking for tartan data patterns:")
        
        # Check for Reference
        ref_match = re.search(r'Reference:\s*(\d+)', content_text)
        print(f"Reference: {ref_match.group(1) if ref_match else 'Not found'}")
        
        # Check for Designer
        designer_match = re.search(r'Designer:\s*([^\n]+)', content_text)
        print(f"Designer: {designer_match.group(1).strip() if designer_match else 'Not found'}")
        
        # Check for Tartan date
        tartan_date_match = re.search(r'Tartan date:\s*([^\n]+)', content_text)
        print(f"Tartan date: {tartan_date_match.group(1).strip() if tartan_date_match else 'Not found'}")
        
        # Check for Registration date
        reg_date_match = re.search(r'Registration date:\s*([^\n]+)', content_text)
        print(f"Registration date: {reg_date_match.group(1).strip() if reg_date_match else 'Not found'}")
        
        # Check for Category
        category_match = re.search(r'Category:\s*([^\n]+)', content_text)
        print(f"Category: {category_match.group(1).strip() if category_match else 'Not found'}")
        
        # Check for Restrictions
        restrictions_match = re.search(r'Restrictions:\s*([^\n]+)', content_text)
        print(f"Restrictions: {restrictions_match.group(1).strip() if restrictions_match else 'Not found'}")
        
        # Check for Registration notes
        notes_match = re.search(r'Registration notes:\s*([^\n]+(?:\n(?!\w+:)[^\n]+)*)', content_text)
        print(f"Registration notes: {notes_match.group(1).strip()[:100] + '...' if notes_match else 'Not found'}")
        
        # Check for Woven Sample
        woven_match = re.search(r'Woven Sample:\s*([^\n]+)', content_text)
        print(f"Woven Sample: {woven_match.group(1).strip() if woven_match else 'Not found'}")
        
        # Check for Registrant details
        registrant_match = re.search(r'Registrant details:\s*([^\n]+)', content_text)
        print(f"Registrant details: {registrant_match.group(1).strip() if registrant_match else 'Not found'}")
        
        # Look for the actual tartan name in the page
        print("\nLooking for tartan name patterns:")
        
        # Try to find the tartan name from the page title
        title_text = soup.title.get_text() if soup.title else ""
        if title_text.startswith('Tartan Details - '):
            tartan_name = title_text.replace('Tartan Details - ', '').strip()
            print(f"From title: {tartan_name}")
        
        # Look for h1 or h2 tags
        headers = soup.find_all(['h1', 'h2'])
        for header in headers:
            text = header.get_text(strip=True)
            if 'Tartan Details' in text:
                print(f"From header: {text}")
        
        # Look for any text that might contain the tartan name
        print("\nSample of page content:")
        print(content_text[:2000])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_tartan_detail()
