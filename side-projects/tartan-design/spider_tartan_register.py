#!/usr/bin/env python3
"""
Spider script for Scottish Register of Tartans
Scrapes tartan data from tartanregister.gov.uk and imports into tartan_designs_register table
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tartan_spider.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TartanSpider:
    def __init__(self):
        self.base_url = "https://www.tartanregister.gov.uk"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.scraped_urls = set()
        self.processed_count = 0
        self.error_count = 0
        
    def get_page(self, url, retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def extract_tartan_links_from_az_page(self, url):
        """Extract tartan detail links from A-Z page"""
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        # Look for links to tartan details pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'tartanDetails' in href and 'ref=' in href:
                full_url = urljoin(self.base_url, href)
                tartan_name = link.get_text(strip=True)
                links.append((full_url, tartan_name))
        
        logger.info(f"Found {len(links)} tartan links on {url}")
        return links
    
    def extract_tartan_data(self, url, tartan_name_from_list=None):
        """Extract tartan data from individual tartan detail page"""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract tartan name from page content
        tartan_name = None
        
        # Look for the tartan name in the breadcrumb navigation
        content_text = soup.get_text()
        breadcrumb_match = re.search(r'you are in:\s*\n\s*([^\n]+)', content_text)
        if breadcrumb_match:
            tartan_name = breadcrumb_match.group(1).strip()
        
        # Fallback: Look for tartan name in quotes
        if not tartan_name:
            quote_match = re.search(r'"([^"]+)" tartan', content_text)
            if quote_match:
                tartan_name = quote_match.group(1)
        
        # Fallback to name from A-Z list if not found
        if not tartan_name and tartan_name_from_list:
            tartan_name = tartan_name_from_list
        
        # Extract data from the details section
        data = {
            'tartan_name': tartan_name,
            'reference': None,
            'designer': None,
            'tartan_date': None,
            'registration_date': None,
            'category': None,
            'restrictions': None,
            'registration_notes': None,
            'woven_sample': None,
            'registrant_details': None,
            'sta_ref': None,
            'stwr_ref': None
        }
        
        # Look for the main content area
        content_area = soup.find('div', class_='content') or soup.find('div', id='content') or soup
        
        # Extract data using text patterns
        text_content = content_area.get_text()
        
        # Extract Reference
        ref_match = re.search(r'Reference:\s*(\d+)', text_content)
        if ref_match:
            data['reference'] = ref_match.group(1)
        
        # Extract Designer
        designer_match = re.search(r'Designer:\s*([^\n]+)', text_content)
        if designer_match:
            data['designer'] = designer_match.group(1).strip()
        
        # Extract Tartan date
        tartan_date_match = re.search(r'Tartan date:\s*([^\n]+)', text_content)
        if tartan_date_match:
            date_str = tartan_date_match.group(1).strip()
            data['tartan_date'] = self.parse_date(date_str)
        
        # Extract Registration date
        reg_date_match = re.search(r'Registration date:\s*([^\n]+)', text_content)
        if reg_date_match:
            date_str = reg_date_match.group(1).strip()
            data['registration_date'] = self.parse_date(date_str)
        
        # Extract Category
        category_match = re.search(r'Category:\s*([^\n]+)', text_content)
        if category_match:
            data['category'] = category_match.group(1).strip()
        
        # Extract Restrictions
        restrictions_match = re.search(r'Restrictions:\s*([^\n]+)', text_content)
        if restrictions_match:
            restrictions = restrictions_match.group(1).strip()
            if restrictions and restrictions != '':
                data['restrictions'] = restrictions
        
        # Extract Registration notes
        notes_match = re.search(r'Registration notes:\s*([^\n]+(?:\n(?!\w+:)[^\n]+)*)', text_content)
        if notes_match:
            data['registration_notes'] = notes_match.group(1).strip()
        
        # Extract Woven Sample
        woven_match = re.search(r'Woven Sample:\s*([^\n]+)', text_content)
        if woven_match:
            woven_text = woven_match.group(1).strip().lower()
            data['woven_sample'] = 'yes' in woven_text or 'received' in woven_text
        
        # Extract Registrant details
        registrant_match = re.search(r'Registrant details:\s*([^\n]+)', text_content)
        if registrant_match:
            data['registrant_details'] = registrant_match.group(1).strip()
        
        # Extract STA ref and STWR ref if present
        sta_match = re.search(r'STA ref:\s*([^\n]+)', text_content)
        if sta_match:
            data['sta_ref'] = sta_match.group(1).strip()
        
        stwr_match = re.search(r'STWR ref:\s*([^\n]+)', text_content)
        if stwr_match:
            data['stwr_ref'] = stwr_match.group(1).strip()
        
        return data
    
    def parse_date(self, date_str):
        """Parse various date formats to YYYY-MM-DD"""
        if not date_str or date_str.strip() == '':
            return None
        
        # Common date formats on the site
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # DD Month YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    try:
                        if '/' in date_str:
                            # DD/MM/YYYY format
                            day, month, year = groups
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        elif any(month_name in date_str.lower() for month_name in 
                                ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            # DD Month YYYY format
                            day, month_name, year = groups
                            month_map = {
                                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                            }
                            month_num = month_map.get(month_name.lower()[:3])
                            if month_num:
                                return f"{year}-{month_num}-{day.zfill(2)}"
                        else:
                            # YYYY-MM-DD format
                            year, month, day = groups
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except (ValueError, IndexError):
                        continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def save_tartan_data(self, data):
        """Save tartan data to database"""
        if not data or not data.get('tartan_name'):
            return False
        
        try:
            with db_manager.get_cursor() as cursor:
                # Check if tartan already exists (by reference or name)
                existing_query = """
                    SELECT id FROM tartan_designs_register 
                    WHERE reference = %s OR tartan_name = %s
                """
                cursor.execute(existing_query, (data['reference'], data['tartan_name']))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    update_query = """
                        UPDATE tartan_designs_register SET
                            tartan_name = %s, reference = %s, designer = %s,
                            tartan_date = %s, registration_date = %s, category = %s,
                            restrictions = %s, registration_notes = %s, woven_sample = %s,
                            registrant_details = %s, sta_ref = %s, stwr_ref = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (
                        data['tartan_name'], data['reference'], data['designer'],
                        data['tartan_date'], data['registration_date'], data['category'],
                        data['restrictions'], data['registration_notes'], data['woven_sample'],
                        data['registrant_details'], data['sta_ref'], data['stwr_ref'],
                        existing['id']
                    ))
                    logger.info(f"Updated tartan: {data['tartan_name']}")
                else:
                    # Insert new record
                    insert_query = """
                        INSERT INTO tartan_designs_register 
                        (tartan_name, reference, designer, tartan_date, registration_date,
                         category, restrictions, registration_notes, woven_sample,
                         registrant_details, sta_ref, stwr_ref)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        data['tartan_name'], data['reference'], data['designer'],
                        data['tartan_date'], data['registration_date'], data['category'],
                        data['restrictions'], data['registration_notes'], data['woven_sample'],
                        data['registrant_details'], data['sta_ref'], data['stwr_ref']
                    ))
                    logger.info(f"Inserted tartan: {data['tartan_name']}")
                
                return True
        except Exception as e:
            logger.error(f"Database error for {data['tartan_name']}: {e}")
            return False
    
    def spider_az_pages(self, letters=None):
        """Spider A-Z pages for tartan links"""
        if letters is None:
            letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        
        all_tartan_links = []
        
        for letter in letters:
            az_url = f"{self.base_url}/az?searchString={letter}"
            logger.info(f"Processing A-Z page for letter: {letter}")
            
            tartan_links = self.extract_tartan_links_from_az_page(az_url)
            all_tartan_links.extend(tartan_links)
            
            # Be respectful - small delay between A-Z pages
            time.sleep(1)
        
        logger.info(f"Total tartan links found: {len(all_tartan_links)}")
        return all_tartan_links
    
    def spider_tartan_details(self, tartan_links):
        """Spider individual tartan detail pages"""
        for url, tartan_name in tartan_links:
            if url in self.scraped_urls:
                continue
            
            logger.info(f"Processing tartan: {tartan_name} ({url})")
            
            data = self.extract_tartan_data(url, tartan_name)
            if data:
                if self.save_tartan_data(data):
                    self.processed_count += 1
                else:
                    self.error_count += 1
            else:
                self.error_count += 1
            
            self.scraped_urls.add(url)
            
            # Be respectful - delay between requests
            time.sleep(0.5)
            
            # Progress update every 50 tartans
            if self.processed_count % 50 == 0:
                logger.info(f"Progress: {self.processed_count} processed, {self.error_count} errors")
    
    def run_full_spider(self, letters=None):
        """Run the complete spidering process"""
        logger.info("Starting tartan spider...")
        
        # Step 1: Get all tartan links from A-Z pages
        tartan_links = self.spider_az_pages(letters)
        
        # Step 2: Process each tartan detail page
        self.spider_tartan_details(tartan_links)
        
        logger.info(f"Spidering complete! Processed: {self.processed_count}, Errors: {self.error_count}")

def main():
    """Main function"""
    spider = TartanSpider()
    
    # You can limit to specific letters for testing
    # spider.run_full_spider(['A', 'B'])  # Test with just A and B
    
    # Run full spider
    spider.run_full_spider()

if __name__ == "__main__":
    main()
