"""
Source Filter

Filters and scores sources based on credibility criteria.
"""

import logging
from typing import Dict, List
from urllib.parse import urlparse

from .config import CREDIBILITY_SCORES, GOOGLE_SEARCH_CREDIBLE_DOMAINS

logger = logging.getLogger(__name__)


class SourceFilter:
    """Filters and scores research sources for credibility"""
    
    def __init__(self):
        """Initialize source filter"""
        self.credible_domains = GOOGLE_SEARCH_CREDIBLE_DOMAINS
    
    def filter_sources(self, sources: List[Dict], min_credibility: float = 0.70) -> List[Dict]:
        """
        Filter sources by credibility score.
        
        Args:
            sources: List of source dictionaries
            min_credibility: Minimum credibility score (0.0-1.0)
            
        Returns:
            Filtered list of sources with credibility scores
        """
        filtered = []
        
        for source in sources:
            # Calculate credibility score
            credibility = self._calculate_credibility(source)
            source['credibility_score'] = credibility
            
            # Filter by minimum credibility
            if credibility >= min_credibility:
                filtered.append(source)
        
        # Sort by credibility (highest first)
        filtered.sort(key=lambda x: x.get('credibility_score', 0), reverse=True)
        
        return filtered
    
    def _calculate_credibility(self, source: Dict) -> float:
        """
        Calculate credibility score for a source.
        
        Args:
            source: Source dictionary with url, domain, source_type
            
        Returns:
            Credibility score (0.0-1.0)
        """
        # Start with base score from source type
        source_type = source.get('source_type', 'other')
        base_score = CREDIBILITY_SCORES.get(source_type, CREDIBILITY_SCORES['other'])
        
        # Check domain credibility
        domain = source.get('domain', '')
        url = source.get('url', '')
        
        if not domain and url:
            domain = self._extract_domain(url)
            source['domain'] = domain
        
        # Boost score for credible domains
        if any(credible_domain in domain.lower() for credible_domain in self.credible_domains):
            base_score = min(1.0, base_score + 0.1)
        
        # Penalize commercial/unknown domains
        if any(x in domain.lower() for x in ['blog', 'wordpress', 'tumblr', 'blogspot']):
            base_score = max(0.3, base_score - 0.2)
        
        return round(base_score, 2)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ''
    
    def classify_source_type(self, url: str, domain: str = None) -> str:
        """
        Classify source type based on URL/domain.
        
        Args:
            url: Source URL
            domain: Source domain (optional, will extract if not provided)
            
        Returns:
            Source type string
        """
        if not domain:
            domain = self._extract_domain(url)
        
        url_lower = url.lower()
        domain_lower = domain.lower()
        
        # Museum sources
        if any(x in domain_lower for x in ['museum', 'nms', 'vam', 'tate', 'nationalgalleries']):
            return 'museum'
        
        # Academic sources
        if '.ac.uk' in domain_lower or '.edu' in domain_lower:
            return 'academic'
        
        # Government sources
        if '.gov.uk' in domain_lower or '.gov' in domain_lower:
            return 'government'
        
        # Wikipedia
        if 'wikipedia' in domain_lower:
            return 'wikipedia'
        
        # Established media (BBC, Scotsman, etc.)
        if any(x in domain_lower for x in ['bbc', 'scotsman', 'herald', 'scotland']):
            return 'established_media'
        
        # Specialist heritage sites
        if any(x in url_lower for x in ['heritage', 'historic', 'clan', 'scottish', 'scotland']):
            return 'specialist_site'
        
        return 'other'

