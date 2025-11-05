#!/usr/bin/env python3
"""
Product Specifications Scraper

Scrapes product specifications (dimensions, materials, etc.) from clan.com product pages.
This data is not available via the API but is published on product pages in structured format.
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)

class ProductSpecificationsScraper:
    """Scraper for product specifications from clan.com product pages"""
    
    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Initialize scraper with rate limiting.
        
        Args:
            rate_limit_delay: Seconds to wait between requests (default: 1.0)
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def scrape_product_specifications(self, product_url: str) -> Optional[Dict[str, str]]:
        """
        Scrape specifications from a product page.
        
        Args:
            product_url: Full URL to the product page
            
        Returns:
            Dictionary of specifications (e.g., {'dimensions': '7" x 8"', 'material': 'Wood'})
            Returns None if scraping fails
        """
        try:
            logger.info(f"Scraping specifications from: {product_url}")
            
            # Fetch page
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            specs = {}
            
            # Method 1: Look for specifications table
            # Common patterns: <table> with <tr><td>Key</td><td>Value</td></tr>
            spec_tables = soup.find_all('table')
            for table in spec_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            # Normalize key names
                            key = self._normalize_key(key)
                            if key:
                                specs[key] = value
            
            # Method 2: Look for definition lists (<dl><dt>Key</dt><dd>Value</dd></dl>)
            dl_elements = soup.find_all('dl')
            for dl in dl_elements:
                terms = dl.find_all('dt')
                definitions = dl.find_all('dd')
                for term, definition in zip(terms, definitions):
                    key = term.get_text(strip=True).lower()
                    value = definition.get_text(strip=True)
                    key = self._normalize_key(key)
                    if key and value:
                        specs[key] = value
            
            # Method 3: Look for specific data attributes or structured divs
            # Clan.com may use specific class names or data attributes
            spec_divs = soup.find_all(['div', 'span'], class_=re.compile(r'spec|detail|attribute', re.I))
            for div in spec_divs:
                text = div.get_text(strip=True)
                # Look for key-value pairs in text
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        key = self._normalize_key(parts[0])
                        value = parts[1].strip()
                        # Clean up value (remove common UI text)
                        value = re.sub(r'(Choose an option|Loading|Choose from)', '', value, flags=re.I).strip()
                        if key and value and len(value) > 2:
                            specs[key] = value
            
            # Method 4: Look for specific patterns in text (fallback)
            page_text = soup.get_text()
            
            # Try to extract dimensions (e.g., "7\" x 8\" or 10\" x 12\"")
            dimensions_match = re.search(r'(\d+["\']?\s*[x×]\s*\d+["\']?(?:\s+or\s+\d+["\']?\s*[x×]\s*\d+["\']?)?)', page_text, re.IGNORECASE)
            if dimensions_match and 'dimensions' not in specs:
                dim_value = dimensions_match.group(1).strip()
                # Only add if it looks like actual dimensions, not a product ID or SKU
                if not re.match(r'^\d+$', dim_value):  # Not just a number
                    specs['dimensions'] = dim_value
            
            # Try to extract material (look for common patterns)
            material_patterns = [
                r'material[s]?:\s*([^\n,\.]+?)(?:\n|$|\.|,|Choose)',
                r'made\s+from\s+([^\n,\.]+?)(?:\n|$|\.|,)',
            ]
            for pattern in material_patterns:
                material_match = re.search(pattern, page_text, re.IGNORECASE)
                if material_match and 'material' not in specs:
                    material_value = material_match.group(1).strip()
                    # Clean up value
                    material_value = re.sub(r'(Choose an option|Loading|Choose from)', '', material_value, flags=re.I).strip()
                    if material_value and len(material_value) > 2:
                        specs['material'] = material_value
                        break
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            if specs:
                logger.info(f"Extracted {len(specs)} specifications: {list(specs.keys())}")
                return specs
            else:
                logger.warning(f"No specifications found on page: {product_url}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request error scraping {product_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping {product_url}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _normalize_key(self, key: str) -> Optional[str]:
        """
        Normalize specification key names to standard format.
        
        Args:
            key: Raw key from page
            
        Returns:
            Normalized key name or None if not a recognized specification
        """
        key = key.lower().strip()
        
        # Mapping of common variations to standard keys
        key_mappings = {
            'dimension': 'dimensions',
            'size': 'dimensions',
            'dimensions': 'dimensions',
            'material': 'material',
            'materials': 'material',
            'made from': 'material',
            'fabric': 'material',
            'emblem': 'emblem',
            'weight': 'weight',
            'care': 'care_instructions',
            'care instructions': 'care_instructions',
            'washing': 'care_instructions',
            'washing instructions': 'care_instructions',
        }
        
        # Check for exact match
        if key in key_mappings:
            return key_mappings[key]
        
        # Check for partial match
        for pattern, normalized in key_mappings.items():
            if pattern in key:
                return normalized
        
        # Return None for unrecognized keys
        return None
    
    def scrape_and_save(self, product_id: int, product_url: str, db_connection) -> bool:
        """
        Scrape specifications and save to database.
        
        Args:
            product_id: Product ID in clan_products table
            product_url: URL to product page
            db_connection: Database connection object
            
        Returns:
            True if successful, False otherwise
        """
        specs = self.scrape_product_specifications(product_url)
        
        if not specs:
            return False
        
        try:
            import json
            with db_connection.cursor() as cur:
                cur.execute("""
                    UPDATE clan_products
                    SET specifications = %s
                    WHERE id = %s
                """, (json.dumps(specs), product_id))
                db_connection.commit()
            
            logger.info(f"Saved specifications for product {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving specifications for product {product_id}: {e}")
            return False


def scrape_product_specifications(product_url: str) -> Optional[Dict[str, str]]:
    """
    Convenience function to scrape specifications from a product URL.
    
    Args:
        product_url: Full URL to the product page
        
    Returns:
        Dictionary of specifications or None if scraping fails
    """
    scraper = ProductSpecificationsScraper()
    return scraper.scrape_product_specifications(product_url)


if __name__ == '__main__':
    # Test with example URL
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        scraper = ProductSpecificationsScraper()
        specs = scraper.scrape_product_specifications(url)
        if specs:
            print("Specifications found:")
            for key, value in specs.items():
                print(f"  {key}: {value}")
        else:
            print("No specifications found")
    else:
        print("Usage: python product_specifications_scraper.py <product_url>")
        print("Example: python product_specifications_scraper.py https://clan.com/clan-crest-wall-plaque")

