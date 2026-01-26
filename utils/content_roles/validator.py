"""
Content Roles Validator

Phase 2.4: Validates generated posts against role constraints.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ContentRoleValidator:
    """
    Validates posts against role-specific constraints.
    
    For DEPTH_LONG:
    - Word count: 120-220 words
    - Paragraph count: ≥ 3
    - Forbidden phrases: buy, order, contact us, etc.
    - Must have source_page_id
    """
    
    # Forbidden phrases for DEPTH_LONG
    DEPTH_LONG_FORBIDDEN_PHRASES = [
        'buy', 'purchase', 'order', 'shop', 'store',
        'contact us', 'call us', 'visit us', 'get in touch',
        'click here', 'learn more', 'read more',
        'sale', 'discount', 'offer', 'deal',
        'we', 'our', 'us'  # Service language
    ]
    
    def validate_depth_long(self, content: str, source_page_id: Optional[int] = None) -> Dict:
        """
        Validate a DEPTH_LONG post.
        
        Args:
            content: Generated post text
            source_page_id: KB article ID (optional, for checking presence)
        
        Returns:
            Dictionary with:
            - valid: bool
            - issues: List of validation issues
            - word_count: Word count
            - paragraph_count: Paragraph count
            - validation_report_json: Structured report
        """
        issues = []
        
        if not content:
            return {
                'valid': False,
                'issues': ['Content is empty'],
                'word_count': 0,
                'paragraph_count': 0,
                'validation_report_json': {'valid': False, 'issues': ['Content is empty']}
            }
        
        # Word count check
        words = content.split()
        word_count = len(words)
        
        if word_count < 120:
            issues.append(f'Word count too low: {word_count} (minimum: 120)')
        elif word_count > 220:
            issues.append(f'Word count too high: {word_count} (maximum: 220)')
        
        # Paragraph count check
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        if paragraph_count < 3:
            issues.append(f'Paragraph count too low: {paragraph_count} (minimum: 3)')
        
        # Forbidden phrase detection
        content_lower = content.lower()
        found_forbidden = []
        
        for phrase in self.DEPTH_LONG_FORBIDDEN_PHRASES:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(phrase.lower()) + r'\b'
            if re.search(pattern, content_lower):
                found_forbidden.append(phrase)
        
        if found_forbidden:
            issues.append(f'Forbidden phrases found: {", ".join(found_forbidden)}')
        
        # Source page check
        if source_page_id is None:
            issues.append('source_page_id is missing (required for DEPTH_LONG)')
        
        # Check for links/CTAs
        if re.search(r'https?://', content):
            issues.append('Links found (not allowed in DEPTH_LONG)')
        
        if re.search(r'(click|read|learn|find out|discover)\s+(more|here|now)', content_lower):
            issues.append('Call-to-action language found (not allowed in DEPTH_LONG)')
        
        # Build validation report
        validation_report = {
            'valid': len(issues) == 0,
            'role': 'DEPTH_LONG',
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'issues': issues,
            'checks': {
                'word_count': {
                    'passed': 120 <= word_count <= 220,
                    'value': word_count,
                    'range': '120-220'
                },
                'paragraph_count': {
                    'passed': paragraph_count >= 3,
                    'value': paragraph_count,
                    'minimum': 3
                },
                'forbidden_phrases': {
                    'passed': len(found_forbidden) == 0,
                    'found': found_forbidden
                },
                'source_page_present': {
                    'passed': source_page_id is not None,
                    'value': source_page_id
                },
                'no_links': {
                    'passed': not re.search(r'https?://', content),
                    'found': bool(re.search(r'https?://', content))
                },
                'no_ctas': {
                    'passed': not re.search(r'(click|read|learn|find out|discover)\s+(more|here|now)', content_lower),
                    'found': bool(re.search(r'(click|read|learn|find out|discover)\s+(more|here|now)', content_lower))
                }
            }
        }
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'word_count': word_count,
            'paragraph_count': paragraph_count,
            'validation_report_json': validation_report
        }
    
    def validate(self, role: str, content: str, **kwargs) -> Dict:
        """
        Validate content for a specific role.
        
        Args:
            role: Role code (e.g., 'DEPTH_LONG')
            content: Generated content
            **kwargs: Role-specific parameters
        
        Returns:
            Validation result dictionary
        """
        if role == 'DEPTH_LONG':
            return self.validate_depth_long(content, kwargs.get('source_page_id'))
        else:
            # Other roles will be implemented in future phases
            return {
                'valid': True,
                'issues': [],
                'validation_report_json': {'valid': True, 'role': role, 'note': 'Validation not yet implemented for this role'}
            }
