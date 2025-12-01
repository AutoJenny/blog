#!/usr/bin/env python3
"""
Producer Web Research

Researches producer information via web search to enrich producer records.
Searches for: location, founding year, heritage details, craftsmanship methods.
"""

import logging
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ProducerResearcher:
    """Researches producer information via web search"""
    
    def __init__(self):
        """Initialize researcher"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def research_producer(self, producer_name: str) -> Dict[str, Optional[str]]:
        """
        Research producer information via web search.
        
        Args:
            producer_name: Name of the producer
            
        Returns:
            Dictionary with research results:
            {
                'location': str or None,
                'founding_year': int or None,
                'heritage_details': str or None,
                'craftsmanship_methods': str or None,
                'website_url': str or None
            }
        """
        logger.info(f"Researching producer: {producer_name}")
        
        research_results = {
            'location': None,
            'founding_year': None,
            'heritage_details': None,
            'craftsmanship_methods': None,
            'website_url': None
        }
        
        try:
            # Search query: "{producer_name} Scotland" or "{producer_name} Scottish"
            search_queries = [
                f"{producer_name} Scotland",
                f"{producer_name} Scottish",
                f"{producer_name} location",
                f"{producer_name} history"
            ]
            
            # For now, we'll use a simple approach:
            # Try to find producer website or Wikipedia page
            # In production, this would use a proper web search API (Google, Bing, etc.)
            
            # Search for common patterns in producer name to find website
            producer_slug = producer_name.lower().replace(' ', '-').replace('&', 'and')
            potential_urls = [
                f"https://www.{producer_slug}.com",
                f"https://www.{producer_slug}.co.uk",
                f"https://{producer_slug}.com",
            ]
            
            for url in potential_urls:
                try:
                    response = self.session.get(url, timeout=5, allow_redirects=True)
                    if response.status_code == 200:
                        research_results['website_url'] = url
                        # Try to extract information from the page
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_text = soup.get_text()
                        
                        # Extract location
                        location = self._extract_location(page_text, producer_name)
                        if location:
                            research_results['location'] = location
                        
                        # Extract founding year
                        founding_year = self._extract_founding_year(page_text)
                        if founding_year:
                            research_results['founding_year'] = founding_year
                        
                        # Extract heritage details
                        heritage = self._extract_heritage(page_text)
                        if heritage:
                            research_results['heritage_details'] = heritage
                        
                        break
                except:
                    continue
            
            # If no website found, try to extract from existing supplier_description
            # This would be called separately with the supplier_description HTML
            
            logger.info(f"Research complete for {producer_name}")
            return research_results
            
        except Exception as e:
            logger.error(f"Error researching producer {producer_name}: {e}")
            return research_results
    
    def _extract_location(self, text: str, producer_name: str) -> Optional[str]:
        """Extract location from text"""
        # Look for common location patterns
        location_patterns = [
            r'based\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'located\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s+Scotland',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Filter out common false positives
                if location.lower() not in ['the', 'a', 'an', 'and', 'or', 'but']:
                    return location
        
        return None
    
    def _extract_founding_year(self, text: str) -> Optional[int]:
        """Extract founding year from text"""
        # Look for patterns like "founded in 1920", "established 1920", "since 1920"
        patterns = [
            r'founded\s+in\s+(\d{4})',
            r'established\s+(\d{4})',
            r'since\s+(\d{4})',
            r'(\d{4})\s+[–-]\s+founded',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                # Sanity check: year should be between 1800 and current year
                current_year = datetime.now().year
                if 1800 <= year <= current_year:
                    return year
        
        return None
    
    def _extract_heritage(self, text: str) -> Optional[str]:
        """Extract heritage details from text"""
        # Look for paragraphs containing heritage-related keywords
        heritage_keywords = ['heritage', 'tradition', 'history', 'craftsmanship', 'traditional', 'scottish', 'scotland']
        
        sentences = re.split(r'[.!?]\s+', text)
        heritage_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in heritage_keywords):
                if len(sentence) > 50:  # Filter out very short sentences
                    heritage_sentences.append(sentence.strip())
        
        if heritage_sentences:
            # Return first 2-3 sentences
            return ' '.join(heritage_sentences[:3])
        
        return None
    
    def enrich_from_supplier_description(self, supplier_description: str) -> Dict[str, Optional[str]]:
        """
        Extract structured data from supplier_description HTML.
        
        Args:
            supplier_description: HTML description from clan_products
            
        Returns:
            Dictionary with extracted information
        """
        if not supplier_description:
            return {}
        
        soup = BeautifulSoup(supplier_description, 'html.parser')
        text = soup.get_text()
        
        results = {}
        
        # Extract location
        location = self._extract_location(text, '')
        if location:
            results['location'] = location
        
        # Extract founding year
        founding_year = self._extract_founding_year(text)
        if founding_year:
            results['founding_year'] = founding_year
        
        # Extract heritage
        heritage = self._extract_heritage(text)
        if heritage:
            results['heritage_details'] = heritage
        
        return results


def research_producer(producer_name: str) -> Dict[str, Optional[str]]:
    """
    Convenience function to research a producer.
    
    Args:
        producer_name: Name of the producer
        
    Returns:
        Dictionary with research results
    """
    researcher = ProducerResearcher()
    return researcher.research_producer(producer_name)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        producer_name = sys.argv[1]
        researcher = ProducerResearcher()
        results = researcher.research_producer(producer_name)
        print(f"\nResearch results for {producer_name}:")
        for key, value in results.items():
            print(f"  {key}: {value}")
    else:
        print("Usage: python producer_research.py <producer_name>")
        print("Example: python producer_research.py 'Lochcarron'")










