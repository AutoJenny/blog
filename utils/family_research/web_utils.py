"""
Web utilities for family research: search, fetching, and text processing.
"""

import os
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import unquote, parse_qs, urlparse


def perform_web_search(query: str, max_results: int = 5) -> List[Dict]:
    """Perform web search and return results."""
    results = []
    
    # Try Google Custom Search API first
    api_key = os.getenv('GOOGLE_SEARCH_API_KEY', '')
    engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')
    
    if api_key and engine_id:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': engine_id,
                'q': query,
                'num': min(max_results, 10)
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', [])[:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'rank': len(results) + 1
                    })
                return results
        except Exception as e:
            print(f"    Google Search API failed: {e}, trying DuckDuckGo...")
    
    # Fallback to DuckDuckGo HTML scraping
    try:
        ddg_url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        params = {'q': query}
        response = requests.get(ddg_url, params=params, headers=headers, timeout=10)
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
            return results
    except Exception as e:
        print(f"    DuckDuckGo search failed: {e}")
    
    return []


def fetch_page_content(url: str) -> Optional[str]:
    """Fetch and extract text content from a web page."""
    try:
        # Fix DuckDuckGo redirect URLs
        if url.startswith('//'):
            # Extract actual URL from DuckDuckGo redirect
            if 'uddg=' in url:
                # Parse the encoded URL
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
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            # Get text
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
    return None


def chunk_text(text: str, chunk_size: int = 3000) -> List[str]:
    """Split text into chunks of approximately chunk_size characters."""
    chunks = []
    words = text.split()
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        if current_size + word_size > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


