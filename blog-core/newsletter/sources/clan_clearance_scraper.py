"""Scraper for clan.com clearance page to extract product data."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install chromium")


def scrape_clearance_page(limit: int = 120) -> List[Dict[str, Any]]:
    """Scrape clearance products from clan.com clearance page.
    
    Args:
        limit: Maximum number of products to scrape (default: 120)
    
    Returns:
        List of product dicts with: url, image_url, title, price_now, price_was, 
        discount_percentage, specifications
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright not available for scraping")
        return []
    
    url = "https://clan.com/products/clearance/?limit=120"
    products = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            logger.info(f"Loading {url} with Playwright...")
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for product grid to load
            try:
                page.wait_for_selector('.product-item, .product-card, [class*="product"]', timeout=10000)
            except Exception:
                logger.warning("Product selector not found, continuing anyway...")
            
            # Give extra time for JavaScript rendering
            page.wait_for_timeout(3000)
            
            # Get page HTML
            html = page.content()
            browser.close()
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product elements - adjust selectors based on actual HTML structure
            # Common patterns: .product-item, .product-card, article.product, etc.
            product_elements = (
                soup.select('.product-item') or
                soup.select('.product-card') or
                soup.select('article.product') or
                soup.select('[class*="product"]') or
                []
            )
            
            logger.info(f"Found {len(product_elements)} product elements on page")
            
            for elem in product_elements[:limit]:
                try:
                    product = parse_product_element(elem, url)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing product element: {e}")
                    continue
            
    except Exception as e:
        logger.error(f"Error scraping clearance page: {e}", exc_info=True)
        return []
    
    logger.info(f"Successfully scraped {len(products)} products from clearance page")
    return products


def parse_product_element(elem: BeautifulSoup, base_url: str) -> Optional[Dict[str, Any]]:
    """Parse a single product element from HTML.
    
    Args:
        elem: BeautifulSoup element containing product data
        base_url: Base URL for resolving relative links
    
    Returns:
        Product dict or None if parsing fails
    """
    try:
        # Extract product URL
        link = elem.find('a', href=True)
        if not link:
            return None
        
        product_url = urljoin(base_url, link['href'])
        
        # Extract product title
        title_elem = (
            elem.find('h2') or
            elem.find('h3') or
            elem.find(class_=re.compile(r'title|name', re.I)) or
            link
        )
        title = title_elem.get_text(strip=True) if title_elem else ''
        
        if not title:
            return None
        
        # Extract image URL
        img = elem.find('img', src=True) or elem.find('img', {'data-src': True})
        if img:
            image_url = img.get('src') or img.get('data-src') or ''
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(base_url, image_url)
        else:
            image_url = ''
        
        # Extract prices
        price_now, price_was = extract_prices(elem)
        
        # Filter out items without valid prices (these are not actual products)
        if not price_now or price_now <= 0:
            return None
        
        # Filter out items with invalid titles (like "Get Our Weekly Newsletter")
        if not title or len(title) < 3:
            return None
        
        # Filter out obvious non-product items
        title_lower = title.lower()
        non_product_keywords = ['newsletter', 'subscribe', 'sign up', 'register', 'login', 'account', 'get our']
        if any(keyword in title_lower for keyword in non_product_keywords):
            return None
        
        # Calculate discount percentage
        discount_percentage = calculate_discount_percentage(price_now, price_was) if price_was else 0.0
        
        # Extract specifications (Colour, Tartan, Fabric, Size, etc.)
        specifications = extract_specifications(elem)
        
        # Also try to extract tartan/colour from product title if not found in specs
        if not specifications.get('Tartan') and not specifications.get('tartan'):
            # Look for tartan names in title (common patterns)
            tartan_patterns = [
                r'\b(MacDonald|MacLeod|MacKenzie|MacNeil|MacGregor|Stewart|Campbell|Gordon|Fraser|Wallace|Bruce|Douglas|Graham|Hamilton|Murray|Robertson|Sinclair|Sutherland|Anderson|Brown|Wilson|Smith|Taylor|Scott|MacDonald Ancient|MacDonald Modern|Royal Stewart|Black Watch)\b',
                r'\b([A-Z][a-z]+\s+(Ancient|Modern|Dress|Weathered|Muted|Reproduction))\b',
            ]
            for pattern in tartan_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    tartan_name = match.group(1) if match.lastindex >= 1 else match.group(0)
                    if len(tartan_name) < 50:  # Reasonable length
                        specifications['Tartan'] = tartan_name
                        break
        
        # Extract product ID from URL if possible
        product_id = extract_product_id_from_url(product_url)
        
        return {
            'product_id': product_id,
            'url': product_url,
            'image_url': image_url,
            'title': title,
            'price_now': price_now,
            'price_was': price_was,
            'discount_percentage': discount_percentage,
            'specifications': specifications
        }
    
    except Exception as e:
        logger.warning(f"Error parsing product element: {e}")
        return None


def extract_prices(elem: BeautifulSoup) -> tuple[float, Optional[float]]:
    """Extract current and original prices from product element.
    
    Returns:
        Tuple of (price_now, price_was) where price_was may be None
    """
    price_now = None
    price_was = None
    
    # Look for price elements - common patterns
    price_selectors = [
        '.price',
        '.product-price',
        '[class*="price"]',
        '.current-price',
        '.sale-price'
    ]
    
    for selector in price_selectors:
        price_elem = elem.select_one(selector)
        if price_elem:
            text = price_elem.get_text(strip=True)
            # Try to extract "now" price
            price_match = re.search(r'[\$£]?([\d,]+\.?\d*)', text.replace(',', ''))
            if price_match:
                try:
                    price_now = float(price_match.group(1))
                    break
                except ValueError:
                    continue
    
    # Look for "was" price - often in a separate element or strikethrough
    was_selectors = [
        '.old-price',
        '.was-price',
        '[class*="was"]',
        'del',
        's',
        '.strikethrough'
    ]
    
    for selector in was_selectors:
        was_elem = elem.select_one(selector)
        if was_elem:
            text = was_elem.get_text(strip=True)
            price_match = re.search(r'[\$£]?([\d,]+\.?\d*)', text.replace(',', ''))
            if price_match:
                try:
                    price_was = float(price_match.group(1))
                    break
                except ValueError:
                    continue
    
    # If no "was" price found, check if there are two prices in the price element
    if not price_was and price_now:
        price_elem = elem.select_one('.price, .product-price, [class*="price"]')
        if price_elem:
            text = price_elem.get_text(strip=True)
            # Look for two prices: "was $X now $Y" or "$X $Y"
            prices = re.findall(r'[\$£]?([\d,]+\.?\d*)', text.replace(',', ''))
            if len(prices) >= 2:
                try:
                    price_was = float(prices[0])
                    price_now = float(prices[1])
                except ValueError:
                    pass
    
    return price_now, price_was


def calculate_discount_percentage(price_now: float, price_was: float) -> float:
    """Calculate discount percentage.
    
    Args:
        price_now: Current price
        price_was: Original price
    
    Returns:
        Discount percentage (0-100)
    """
    if not price_was or price_was <= 0:
        return 0.0
    
    if price_now >= price_was:
        return 0.0
    
    discount = ((price_was - price_now) / price_was) * 100
    return round(discount, 2)


def extract_specifications(elem: BeautifulSoup) -> Dict[str, str]:
    """Extract product specifications (Colour, Tartan, Fabric, Size, etc.).
    
    Returns:
        Dict with specification keys and values
    """
    specs = {}
    
    # Valid specification keys (common product attributes)
    # Be very conservative - only universally applicable specs
    valid_spec_keys = {
        'colour', 'color', 'tartan', 'fabric', 'material', 'pattern', 'style', 'finish'
    }
    
    # Size-related specs that should only be included if value is very short and simple
    size_spec_keys = {
        'size', 'width', 'length'
    }
    
    # Invalid specification values (likely page text, not product specs)
    invalid_value_patterns = [
        r'rgb\([^)]+\)',  # CSS color values
        r'\.svg',  # File extensions
        r'\.jpg|\.png|\.gif',  # Image file extensions
        r'http://|https://',  # URLs
        r'^\d+$',  # Just numbers
        r'^\d+\s+years?$',  # Age (usually not a product spec)
        r'page\s+\d+',  # Page numbers
        r'note:',  # Notes
        r'we charge',  # Payment notes
        r'convert',  # Currency conversion notes
    ]
    
    # Look for structured spec elements first (more reliable)
    spec_elements = elem.select('[class*="spec"], [class*="attribute"], [data-attribute], [class*="detail"]')
    for spec_elem in spec_elements:
        label = spec_elem.get('data-label') or spec_elem.get('data-attribute')
        value = spec_elem.get('data-value')
        
        # Try to find label and value in child elements
        if not label:
            label_elem = spec_elem.find(class_=re.compile(r'label|name|key', re.I))
            if label_elem:
                label = label_elem.get_text(strip=True)
        
        if not value:
            value_elem = spec_elem.find(class_=re.compile(r'value|data|content', re.I))
            if value_elem:
                value = value_elem.get_text(strip=True)
        
        if label and value:
            label_text = label.strip()
            value_text = value.strip()
            
            # Validate the spec - allow valid product specs but filter out nonsense
            label_lower = label_text.lower()
            
            # Only include universally applicable specs (colour, tartan, fabric, material)
            # For size-related specs, be extra strict
            is_valid_key = label_lower in valid_spec_keys
            is_size_key = label_lower in size_spec_keys
            
            if is_valid_key or is_size_key:
                # Validation for all specs - allow valid product attributes
                if (value_text and 
                    len(value_text) < 80 and  # Reasonable max length
                    len(value_text.split()) < 8 and  # Max 8 words (allow longer tartan names)
                    not any(re.search(pattern, value_text, re.IGNORECASE) for pattern in invalid_value_patterns) and
                    not re.search(r'/\w+\.(svg|jpg|png)', value_text, re.IGNORECASE) and  # No file paths
                    not re.search(r'rgb\(', value_text, re.IGNORECASE) and  # No CSS colors
                    label_lower not in ['clan', 'crest', 'engraving', 'age', 'name', 'motto', 'note', 'page', 'waist', 'chest', 'collar', 'fitting', 'height', 'depth']):
                    # For size keys, extra validation - must be very short and simple
                    if is_size_key:
                        if (len(value_text) < 30 and 
                            len(value_text.split()) < 4 and
                            not re.search(r'\d+\s*(years?|cm|inches?|"|\')', value_text, re.IGNORECASE)):  # No measurements
                            specs[label_text] = value_text
                    else:
                        # For valid keys (colour, tartan, fabric, etc.), allow them if they're reasonable
                        # Allow colons in tartan names (e.g., "MacDonald Ancient")
                        if ':' not in value_text or label_lower == 'tartan':  # Allow colons only in tartan
                            specs[label_text] = value_text
    
    # Use text-based extraction - look for specs in the element text
    # This is important because many product pages don't have structured spec elements
    spec_text = elem.get_text()
    
    # Look for patterns like "Tartan: MacDonald" or "Colour: Black"
    # Try to extract valid product specs from the text
    for spec_key in valid_spec_keys:
        # Skip if already found
        if spec_key.lower() in [k.lower() for k in specs.keys()]:
            continue
        
        # Pattern: "SpecKey: Value" (case insensitive)
        # Allow flexible spacing and punctuation
        pattern = rf'(?:^|\s|>){spec_key}\s*:\s*([^\n\r<>{{}}]{1,70}?)(?:\s*[,\n\r<]|$)'
        matches = re.finditer(pattern, spec_text, re.IGNORECASE)
        
        for match in matches:
            value = match.group(1).strip()
            
            # Clean up value - remove trailing punctuation
            value = value.rstrip('.,;')
            
            # Validate the value - be more lenient for valid product specs
            if (value and 
                len(value) > 0 and
                len(value) < 80 and
                len(value.split()) < 12 and  # Allow longer values for tartan/pattern names
                not any(re.search(p, value, re.IGNORECASE) for p in invalid_value_patterns) and
                not re.search(r'/\w+\.(svg|jpg|png|gif)', value, re.IGNORECASE) and
                not re.search(r'rgb\(', value, re.IGNORECASE) and
                not re.search(r'\d+\s*years?', value, re.IGNORECASE) and  # No age
                not re.search(r'page\s+\d+', value, re.IGNORECASE) and  # No page numbers
                'we charge' not in value.lower() and  # No payment notes
                'convert' not in value.lower() and  # No currency conversion
                not value.lower().startswith('http') and  # No URLs
                len(value) > 1):  # Must be at least 2 chars
                
                # Special handling for tartan - allow longer names
                if spec_key == 'tartan':
                    if len(value) < 100 and len(value.split()) < 12:
                        specs[spec_key.capitalize()] = value
                        break  # Found tartan, move to next spec key
                else:
                    # For other specs, be more strict about nested colons
                    # But allow simple cases like "Colour: Red" even if there's more text after
                    if ':' not in value or len(value.split(':')) == 1:
                        specs[spec_key.capitalize()] = value
                        break  # Found this spec, move to next spec key
    
    return specs


def extract_product_id_from_url(url: str) -> Optional[int]:
    """Extract product ID from URL if possible.
    
    Args:
        url: Product URL
    
    Returns:
        Product ID or None
    """
    # Common patterns: /products/123, /product/123, /clearance-123, ?id=123
    patterns = [
        r'/products?/(\d+)',  # /products/123 or /product/123
        r'/clearance-(\d+)',  # /clearance-123
        r'[?&]id=(\d+)',  # ?id=123
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None

