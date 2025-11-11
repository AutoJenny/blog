"""
Wikipedia Researcher

Fetches content and references from Wikipedia for heritage research.
Uses wikipedia-api library for structured access.
"""

import logging
import re
from typing import Dict, List, Optional

try:
    import wikipediaapi
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("wikipedia-api library not installed. Wikipedia research will be unavailable.")

logger = logging.getLogger(__name__)


class WikipediaResearcher:
    """Researches category heritage using Wikipedia API"""
    
    def __init__(self, language: str = 'en'):
        """
        Initialize Wikipedia researcher.
        
        Args:
            language: Wikipedia language code (default: 'en')
        """
        if not WIKIPEDIA_AVAILABLE:
            raise ImportError("wikipedia-api library is not installed. Install with: pip install wikipedia-api")
        
        self.language = language
        # wikipedia-api requires user_agent as first parameter
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='CLAN Heritage Research/1.0 (https://clan.com)',
            language=language
        )
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search Wikipedia for articles matching query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of article summaries with metadata
        """
        try:
            import requests
            
            # Use Wikipedia REST API for search
            search_url = f"https://{self.language}.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
            
            # Try direct page access first
            try:
                response = requests.get(search_url, headers={'User-Agent': 'CLAN Heritage Research/1.0 (https://clan.com)'})
                if response.status_code == 200:
                    data = response.json()
                    return [{
                        'title': data.get('title', query),
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'summary': data.get('extract', '')[:500],
                        'word_count': len(data.get('extract', '').split())
                    }]
            except:
                pass
            
            # If direct access fails, use search API
            search_api_url = f"https://{self.language}.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': max_results,
                'format': 'json'
            }
            
            response = requests.get(search_api_url, params=params, 
                                   headers={'User-Agent': 'CLAN Heritage Research/1.0 (https://clan.com)'})
            
            if response.status_code != 200:
                logger.warning(f"Wikipedia search API returned status {response.status_code}")
                return []
            
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            articles = []
            for result in search_results[:max_results]:
                title = result.get('title', '')
                page = self.wiki.page(title)
                if page.exists():
                    articles.append({
                        'title': page.title,
                        'url': page.fullurl,
                        'summary': page.summary[:500] if page.summary else '',
                        'word_count': len(page.summary.split()) if page.summary else 0
                    })
            
            logger.info(f"Wikipedia search for '{query}' returned {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching Wikipedia for '{query}': {e}")
            return []
    
    def get_page(self, title: str) -> Optional[Dict]:
        """
        Get full Wikipedia page content.
        
        Args:
            title: Wikipedia page title
            
        Returns:
            Dictionary with page content and metadata, or None if not found
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                logger.warning(f"Wikipedia page '{title}' does not exist")
                return None
            
            # Extract references from page text
            references = self._extract_references(page.text)
            
            return {
                'title': page.title,
                'url': page.fullurl,
                'summary': page.summary,
                'content': page.text,  # Full content, not truncated
                'word_count': len(page.text.split()),
                'references': references,
                'categories': list(page.categories.keys())[:10] if page.categories else []
            }
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia page '{title}': {e}")
            return None
    
    def _extract_references(self, text: str) -> List[Dict]:
        """
        Extract references from Wikipedia page text.
        
        Args:
            text: Wikipedia page text
            
        Returns:
            List of reference dictionaries with URLs and titles
        """
        references = []
        
        # Pattern to match Wikipedia reference tags: <ref>...</ref>
        # This is a simplified extraction - full Wikipedia parsing would be more complex
        ref_pattern = r'<ref[^>]*>(.*?)</ref>'
        ref_matches = re.findall(ref_pattern, text, re.DOTALL)
        
        # Extract URLs from references
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        for ref_text in ref_matches[:20]:  # Limit to first 20 references
            urls = re.findall(url_pattern, ref_text)
            for url in urls:
                # Filter for credible domains
                if any(domain in url for domain in ['.ac.uk', '.gov.uk', '.edu', 'museum', 'nls.uk', 'historicenvironment.scot']):
                    references.append({
                        'url': url,
                        'domain': self._extract_domain(url),
                        'source_type': self._classify_source(url)
                    })
        
        return references
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ''
    
    def _classify_source(self, url: str) -> str:
        """Classify source type based on URL"""
        url_lower = url.lower()
        
        if any(x in url_lower for x in ['museum', 'nms', 'vam', 'tate']):
            return 'museum'
        elif any(x in url_lower for x in ['.ac.uk', '.edu']):
            return 'academic'
        elif any(x in url_lower for x in ['.gov.uk', '.gov']):
            return 'government'
        elif 'wikipedia' in url_lower:
            return 'wikipedia'
        else:
            return 'other'
    
    def research_dimension(self, queries: List[str], dimension: str) -> Dict:
        """
        Research a specific dimension using Wikipedia.
        
        Args:
            queries: List of Wikipedia article titles/queries for this dimension
            dimension: Research dimension name
            
        Returns:
            Dictionary with research results
        """
        sources = []
        seen_titles = set()
        
        # Try each query - get full page content, not just snippets
        for query in queries[:5]:  # Limit to 5 queries per dimension
            try:
                # Try direct page access first (most reliable)
                page_data = self.get_page(query)
                
                if page_data and page_data['title'] not in seen_titles:
                    seen_titles.add(page_data['title'])
                    
                    # Get full text content (not just summary)
                    full_text = page_data.get('content', '')
                    summary = page_data.get('summary', '')
                    
                    # Extract relevant sections based on dimension
                    relevant_content = self._extract_relevant_content(full_text, dimension, query)
                    
                    sources.append({
                        'title': page_data['title'],
                        'url': page_data['url'],
                        'domain': self._extract_domain(page_data['url']),
                        'source_type': 'wikipedia',
                        'summary': summary,
                        'full_content': relevant_content,  # Full relevant content, not just snippets
                        'word_count': len(relevant_content.split()),
                        'references': page_data.get('references', [])
                    })
            except Exception as e:
                logger.debug(f"Could not fetch page '{query}': {e}")
                # Try search as fallback
                search_results = self.search(query, max_results=3)
                for article in search_results:
                    if article['title'] not in seen_titles:
                        page_data = self.get_page(article['title'])
                        if page_data:
                            seen_titles.add(page_data['title'])
                            full_text = page_data.get('content', '')
                            relevant_content = self._extract_relevant_content(full_text, dimension, query)
                            
                            sources.append({
                                'title': page_data['title'],
                                'url': page_data['url'],
                                'domain': self._extract_domain(page_data['url']),
                                'source_type': 'wikipedia',
                                'summary': page_data.get('summary', ''),
                                'full_content': relevant_content,
                                'word_count': len(relevant_content.split()),
                                'references': page_data.get('references', [])
                            })
                        break  # Only use first search result as fallback
        
        return {
            'dimension': dimension,
            'queries': queries,
            'sources': sources,
            'total_sources': len(sources),
            'research_method': 'wikipedia_api'
        }
    
    def _extract_relevant_content(self, full_text: str, dimension: str, query: str) -> str:
        """
        Extract relevant content from full Wikipedia page text based on dimension.
        
        Args:
            full_text: Full Wikipedia page text
            dimension: Research dimension
            query: Original query
            
        Returns:
            Relevant content text
        """
        # For now, return first 5000 characters (can be enhanced with section extraction)
        # In future, could extract specific sections like "History", "Cultural significance", etc.
        if len(full_text) <= 5000:
            return full_text
        
        # Try to find relevant sections
        dimension_keywords = {
            'historical_origins': ['history', 'origin', 'early', 'first', 'developed', 'began', 'century'],
            'cultural_significance': ['culture', 'significance', 'tradition', 'heritage', 'identity', 'meaning'],
            'evolution': ['evolution', 'change', 'develop', 'modern', 'adapt', 'transform'],
            'scottish_heritage_connections': ['scotland', 'scottish', 'clan', 'highland', 'regional', 'tradition'],
            'industrial_legacy': ['manufacture', 'producer', 'industry', 'craft', 'traditional', 'process']
        }
        
        keywords = dimension_keywords.get(dimension, [])
        
        # Split into sentences and prioritize those with relevant keywords
        sentences = full_text.split('.')
        relevant_sentences = []
        other_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                relevant_sentences.append(sentence)
            else:
                other_sentences.append(sentence)
        
        # Combine: relevant sentences first, then others up to limit
        combined = '. '.join(relevant_sentences + other_sentences[:50])
        
        # Limit to 5000 characters
        if len(combined) > 5000:
            combined = combined[:5000] + '...'
        
        return combined or full_text[:5000]
    
    def _extract_snippets(self, text: str, query: str, max_snippets: int = 5) -> List[str]:
        """
        Extract relevant snippets from text based on query.
        
        Args:
            text: Text to extract from
            query: Query terms to find relevant snippets
            max_snippets: Maximum number of snippets to return
            
        Returns:
            List of text snippets
        """
        # Simple snippet extraction: find sentences containing query terms
        query_terms = query.lower().split()
        sentences = re.split(r'[.!?]+', text)
        
        snippets = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Count how many query terms appear in sentence
            matches = sum(1 for term in query_terms if term in sentence_lower)
            if matches >= 2 and len(sentence.strip()) > 50:  # At least 2 terms and meaningful length
                snippets.append(sentence.strip()[:300])  # Max 300 chars per snippet
                if len(snippets) >= max_snippets:
                    break
        
        return snippets

