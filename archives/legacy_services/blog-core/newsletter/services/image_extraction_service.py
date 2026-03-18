"""Extract images from article pages with captions and credits.

This service fetches article HTML, extracts images from the same domain,
and captures associated captions and credits for copyright compliance.
"""

from __future__ import annotations

import logging
import requests
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class ImageExtractionService:
    """Service for extracting images from article pages."""
    
    def __init__(self, timeout: int = 10, max_images: int = 10):
        """Initialize with timeout and max images per article."""
        self.timeout = timeout
        self.max_images = max_images
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0; +https://example.com/bot)'
        })
    
    def extract_images(self, article_url: str, source_domain: str) -> List[Dict[str, str]]:
        """Extract images from an article page.
        
        Args:
            article_url: Full URL of the article
            source_domain: Domain of the source (e.g., 'example.com')
        
        Returns:
            List of image dicts with keys: url, caption, credit, domain
        """
        try:
            # Fetch article page
            response = self.session.get(article_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            parsed_url = urlparse(article_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Extract all images
            images = []
            img_tags = soup.find_all('img', src=True)
            
            for img_tag in img_tags[:self.max_images * 2]:  # Check more than max to filter
                img_data = self._extract_image_data(img_tag, base_url, source_domain)
                if img_data:
                    images.append(img_data)
                    if len(images) >= self.max_images:
                        break
            
            logger.info(f"Extracted {len(images)} images from {article_url}")
            return images
            
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch article for image extraction: {article_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting images from {article_url}: {e}", exc_info=True)
            return []
    
    def _extract_image_data(self, img_tag: Tag, base_url: str, source_domain: str) -> Optional[Dict[str, str]]:
        """Extract data from a single img tag."""
        src = img_tag.get('src', '').strip()
        if not src:
            return None
        
        # Convert to absolute URL
        if src.startswith('//'):
            src = f"https:{src}"
        elif src.startswith('/'):
            src = urljoin(base_url, src)
        elif not src.startswith('http'):
            src = urljoin(base_url, src)
        
        # Filter: must be from same domain
        parsed_src = urlparse(src)
        if parsed_src.netloc and parsed_src.netloc != source_domain:
            # Check if it's a subdomain (e.g., cdn.example.com)
            if not parsed_src.netloc.endswith(f'.{source_domain}') and source_domain not in parsed_src.netloc:
                return None  # Different domain, likely ad/tracker
        
        # Skip data URIs and very small images (likely icons)
        if src.startswith('data:'):
            return None
        
        # Extract caption
        caption = self._extract_caption(img_tag)
        
        # Extract credit
        credit = self._extract_credit(img_tag)
        
        return {
            'url': src,
            'caption': caption,
            'credit': credit,
            'domain': parsed_src.netloc or source_domain
        }
    
    def _extract_caption(self, img_tag: Tag) -> str:
        """Extract caption from img tag or nearby elements."""
        # Try figcaption (most common)
        parent = img_tag.find_parent(['figure', 'div'])
        if parent:
            figcaption = parent.find('figcaption')
            if figcaption:
                return figcaption.get_text().strip()
            
            # Try caption class
            caption_elem = parent.find(class_=lambda x: x and 'caption' in x.lower())
            if caption_elem:
                return caption_elem.get_text().strip()
        
        # Try alt text
        alt = img_tag.get('alt', '').strip()
        if alt and len(alt) > 10:  # Only use if substantial
            return alt
        
        # Try title attribute
        title = img_tag.get('title', '').strip()
        if title and len(title) > 10:
            return title
        
        # Try next sibling paragraph
        next_sibling = img_tag.find_next_sibling(['p', 'div'])
        if next_sibling:
            text = next_sibling.get_text().strip()
            if text and len(text) < 200:  # Likely a caption if short
                return text
        
        return ''
    
    def _extract_credit(self, img_tag: Tag) -> str:
        """Extract photo credit from img tag or nearby elements."""
        # Try data attributes
        for attr in ['data-credit', 'data-photographer', 'data-photo-credit', 'data-author']:
            credit = img_tag.get(attr, '').strip()
            if credit:
                return credit
        
        # Try credit class in parent
        parent = img_tag.find_parent(['figure', 'div', 'article'])
        if parent:
            credit_elem = parent.find(class_=lambda x: x and 'credit' in x.lower())
            if credit_elem:
                text = credit_elem.get_text().strip()
                # Common patterns
                if any(marker in text.lower() for marker in ['photo', 'image', 'credit', '©', '(c)']):
                    return text
            
            # Look for credit in nearby text (often after caption)
            for sibling in parent.find_all(['p', 'span', 'div']):
                text = sibling.get_text().strip()
                if any(marker in text.lower() for marker in ['photo:', 'image:', 'credit:', '©', 'photograph']):
                    return text
        
        return ''


def extract_images_for_article(article_url: str, source_domain: str, 
                               timeout: int = 10, max_images: int = 10) -> List[Dict[str, str]]:
    """Convenience function to extract images from an article.
    
    Args:
        article_url: Full URL of the article
        source_domain: Domain of the source
        timeout: Request timeout in seconds
        max_images: Maximum number of images to extract
    
    Returns:
        List of image dicts
    """
    service = ImageExtractionService(timeout=timeout, max_images=max_images)
    return service.extract_images(article_url, source_domain)

