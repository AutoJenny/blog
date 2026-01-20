"""
Source Evaluator
Evaluates and prioritizes sources based on domain authority and reliability.
"""

import re
from typing import Dict, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class SourceEvaluator:
    """Evaluates source reliability and assigns priority tiers."""
    
    # Domain patterns for different tiers
    TIER_1_DOMAINS = [
        r'\.edu$',
        r'\.gov\.uk$',
        r'\.ac\.uk$',
        r'museum',
        r'archive',
        r'national.*scotland',
        r'historic.*scotland',
        r'visitscotland',
    ]
    
    TIER_2_DOMAINS = [
        r'heritage',
        r'history',
        r'historic.*environment',
        r'local.*history',
        r'traditional.*food',
        r'culinary.*heritage',
    ]
    
    TIER_3_DOMAINS = [
        r'wikipedia',
        r'britannica',
        r'encyclopedia',
        r'food.*history',
        r'culinary.*archive',
    ]
    
    # Academic indicators
    ACADEMIC_INDICATORS = [
        'university',
        'college',
        'academic',
        'scholar',
        'research',
        'journal',
        'thesis',
        'dissertation'
    ]
    
    def get_domain_tier(self, url: str) -> int:
        """
        Get domain tier (1=highest, 4=lowest) based on URL.
        
        Args:
            url (str): Source URL
        
        Returns:
            int: Tier number (1-4)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check Tier 1 (Academic/Government/Museum)
            for pattern in self.TIER_1_DOMAINS:
                if re.search(pattern, domain):
                    return 1
            
            # Check Tier 2 (Heritage/Cultural)
            for pattern in self.TIER_2_DOMAINS:
                if re.search(pattern, domain):
                    return 2
            
            # Check Tier 3 (Authoritative Reference)
            for pattern in self.TIER_3_DOMAINS:
                if re.search(pattern, domain):
                    return 3
            
            # Default to Tier 4 (General web)
            return 4
        except Exception as e:
            logger.warning(f"Error evaluating domain tier for {url}: {e}")
            return 4
    
    def is_academic_source(self, url: str) -> bool:
        """
        Check if URL appears to be from an academic source.
        
        Args:
            url (str): Source URL
        
        Returns:
            bool: True if appears academic
        """
        domain_tier = self.get_domain_tier(url)
        if domain_tier == 1:
            return True
        
        # Check for academic indicators in URL
        url_lower = url.lower()
        for indicator in self.ACADEMIC_INDICATORS:
            if indicator in url_lower:
                return True
        
        return False
    
    def evaluate_reliability(self, url: str, domain: str = None) -> Dict:
        """
        Evaluate source reliability and return assessment.
        
        Args:
            url (str): Source URL
            domain (str, optional): Domain name (extracted if not provided)
        
        Returns:
            dict: Reliability assessment with 'tier', 'is_academic', 'reliability_score'
        """
        if domain is None:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
            except:
                domain = ''
        
        tier = self.get_domain_tier(url)
        is_academic = self.is_academic_source(url)
        
        # Reliability score (0-100)
        reliability_score = {
            1: 90,  # Academic/Government/Museum
            2: 75,  # Heritage/Cultural
            3: 60,  # Authoritative Reference
            4: 40   # General web
        }.get(tier, 40)
        
        # Boost for academic sources
        if is_academic and tier > 1:
            reliability_score = min(100, reliability_score + 10)
        
        reliability_label = {
            1: 'high',
            2: 'medium-high',
            3: 'medium',
            4: 'low'
        }.get(tier, 'low')
        
        return {
            'tier': tier,
            'is_academic': is_academic,
            'reliability_score': reliability_score,
            'reliability': reliability_label,
            'domain': domain
        }
    
    def prioritize_sources(self, results: List[Dict]) -> List[Dict]:
        """
        Prioritize search results by reliability.
        
        Args:
            results (list): List of search result dicts with 'url'
        
        Returns:
            list: Sorted list with highest priority first
        """
        # Evaluate each result
        for result in results:
            url = result.get('url', '')
            evaluation = self.evaluate_reliability(url)
            result['domain_tier'] = evaluation['tier']
            result['reliability'] = evaluation['reliability']
            result['reliability_score'] = evaluation['reliability_score']
            result['is_academic'] = evaluation['is_academic']
        
        # Sort by tier (ascending), then by reliability_score (descending)
        results.sort(key=lambda x: (x.get('domain_tier', 4), -x.get('reliability_score', 0)))
        
        return results
    
    def filter_by_domain_authority(self, results: List[Dict], min_tier: int = 4) -> List[Dict]:
        """
        Filter results to only include sources above minimum tier.
        
        Args:
            results (list): List of search result dicts
            min_tier (int): Minimum tier to include (1=highest, 4=lowest)
        
        Returns:
            list: Filtered results
        """
        return [
            result for result in results
            if result.get('domain_tier', 4) <= min_tier
        ]
