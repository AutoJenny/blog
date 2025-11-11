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
        self.wiki = wikipediaapi.Wikipedia(
            language=language,
            user_agent='CLAN Heritage Research/1.0'
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
            # Wikipedia API search
            search_results = self.wiki.search(query, results=max_results)
            
            articles = []
            for title in search_results:
                page = self.wiki.page(title)
                if page.exists():
                    articles.append({
                        'title': page.title,
                        'url': page.fullurl,
                        'summary': page.summary[:500] if page.summary else '',  # First 500 chars
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
                'content': page.text[:5000],  # First 5000 chars
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
    
    def research_dimension(self, query: str, dimension: str) -> Dict:
        """
        Research a specific dimension using Wikipedia.
        
        Args:
            query: Search query for this dimension
            dimension: Research dimension name
            
        Returns:
            Dictionary with research results
        """
        # Search for relevant articles
        articles = self.search(query, max_results=10)
        
        # Get full content for top articles
        sources = []
        for article in articles[:5]:  # Top 5 articles
            page_data = self.get_page(article['title'])
            if page_data:
                sources.append({
                    'title': page_data['title'],
                    'url': page_data['url'],
                    'domain': self._extract_domain(page_data['url']),
                    'source_type': 'wikipedia',
                    'summary': page_data['summary'],
                    'snippets': self._extract_snippets(page_data['content'], query),
                    'references': page_data['references']
                })
        
        return {
            'dimension': dimension,
            'query': query,
            'sources': sources,
            'total_sources': len(sources),
            'research_method': 'wikipedia_api'
        }
    
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

