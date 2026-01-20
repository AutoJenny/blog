"""
Web Researcher
Handles web search and content fetching for research topics.
"""

import os
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import unquote, parse_qs, urlparse
import logging

logger = logging.getLogger(__name__)


class WebResearcher:
    """Performs web search and fetches content from URLs."""
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY', '')
        self.google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Perform web search and return results.
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
        
        Returns:
            list: List of search result dicts with 'title', 'url', 'snippet', 'rank'
        """
        results = []
        
        # Try Google Custom Search API first
        if self.google_api_key and self.google_engine_id:
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_engine_id,
                    'q': query,
                    'num': min(max_results, 10)
                }
                response = requests.get(url, params=params, timeout=20)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', [])[:max_results]:
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'rank': len(results) + 1
                        })
                    if results:
                        logger.info(f"Found {len(results)} results via Google Search API")
                        return results
            except Exception as e:
                logger.warning(f"Google Search API failed: {e}, trying DuckDuckGo...")
        
        # Fallback to DuckDuckGo HTML scraping
        try:
            ddg_url = "https://html.duckduckgo.com/html/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {'q': query}
            response = requests.get(ddg_url, params=params, headers=headers, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for i, result in enumerate(soup.select('.result')[:max_results]):
                    title_elem = result.select_one('.result__a')
                    snippet_elem = result.select_one('.result__snippet')
                    if title_elem:
                        url = title_elem.get('href', '')
                        # Extract actual URL from DuckDuckGo redirect
                        if url.startswith('//') and 'uddg=' in url:
                            try:
                                parsed = urlparse('https:' + url)
                                if 'uddg' in parsed.query:
                                    params = parse_qs(parsed.query)
                                    if 'uddg' in params:
                                        url = unquote(params['uddg'][0])
                            except:
                                pass
                        elif url.startswith('//'):
                            url = 'https:' + url
                        
                        results.append({
                            'title': title_elem.get_text(strip=True),
                            'url': url,
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'rank': len(results) + 1
                        })
                if results:
                    logger.info(f"Found {len(results)} results via DuckDuckGo")
                    return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        logger.warning(f"No search results found for query: {query}")
        return []
    
    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a web page.
        
        Args:
            url (str): URL to fetch
        
        Returns:
            str: Extracted text content, or None if fetch failed
        """
        try:
            # Fix DuckDuckGo redirect URLs
            if url.startswith('//'):
                if 'uddg=' in url:
                    parsed = urlparse('https:' + url)
                    if 'uddg' in parsed.query:
                        params = parse_qs(parsed.query)
                        if 'uddg' in params:
                            url = unquote(params['uddg'][0])
                else:
                    url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                # Get text
                text = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                return text
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
        return None
