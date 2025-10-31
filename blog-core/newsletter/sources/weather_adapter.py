"""Weather adapter for scraping weather reports and forecasts from HTML pages."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import logging
import re
from newsletter.sources.base import SourceAdapter

logger = logging.getLogger(__name__)


class WeatherHTMLAdapter(SourceAdapter):
    """Adapter for scraping weather information from BBC/Met Office HTML pages."""
    
    def __init__(self, source_name: str, base_url: str, category: str = 'weather', rate_limit_minutes: int = 60):
        """Initialize weather adapter.
        
        Args:
            source_name: Name of source (e.g., "BBC Scotland Weather")
            base_url: Base URL to scrape (forecast or report page)
            category: Content category (default: 'weather')
            rate_limit_minutes: Minutes between fetches (default: 60 for weather)
        """
        super().__init__(source_name, rate_limit_minutes)
        self.base_url = base_url
        self.category = category
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
        }
    
    def _extract_weather_data(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract weather data from HTML.
        
        Returns list of weather items (reports or forecasts).
        """
        items = []
        
        # Determine if this is a forecast or report page
        is_forecast = any(term in url.lower() for term in ['forecast', 'outlook', '5-day', '7-day'])
        
        # Extract current/recent weather reports
        # BBC Scotland weather structure
        if 'bbc' in url.lower():
            # Try to extract forecast data
            forecast_elements = soup.select('.weather-day, .forecast-day, [class*="forecast"]')
            
            for elem in forecast_elements[:7]:  # Up to 7 days
                date_elem = elem.select_one('.date, time, [datetime]')
                condition_elem = elem.select_one('.condition, .weather-type, [class*="condition"]')
                temp_elem = elem.select_one('.temperature, .temp, [class*="temp"]')
                
                if date_elem or condition_elem:
                    date_text = ''
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    
                    condition = condition_elem.get_text(strip=True) if condition_elem else ''
                    temp = temp_elem.get_text(strip=True) if temp_elem else ''
                    
                    title = f"Weather: {condition}"
                    if temp:
                        title += f" {temp}"
                    if date_text:
                        title += f" ({date_text})"
                    
                    items.append({
                        'title': title,
                        'url': url,
                        'date_text': date_text,
                        'condition': condition,
                        'temperature': temp,
                        'is_forecast': is_forecast,
                        'type': 'forecast' if is_forecast else 'report',
                    })
            
            # If no structured forecast found, try to extract summary
            if not items:
                summary_elem = soup.select_one('.weather-summary, .current-weather, [class*="summary"]')
                if summary_elem:
                    summary_text = summary_elem.get_text(strip=True)[:200]
                    items.append({
                        'title': f"Weather Update: {summary_text}",
                        'url': url,
                        'date_text': datetime.now().strftime('%Y-%m-%d'),
                        'condition': summary_text,
                        'is_forecast': False,
                        'type': 'report',
                    })
        
        # Met Office structure
        elif 'metoffice' in url.lower():
            # Met Office often uses structured data
            warnings_elem = soup.select_one('.weather-warning, .alert, [class*="warning"]')
            if warnings_elem:
                warning_text = warnings_elem.get_text(strip=True)
                items.append({
                    'title': f"Weather Warning: {warning_text[:100]}",
                    'url': url,
                    'date_text': datetime.now().strftime('%Y-%m-%d'),
                    'condition': warning_text,
                    'is_forecast': False,
                    'type': 'warning',
                })
            
            # Extract forecast if available
            forecast_section = soup.select_one('.forecast-content, [class*="forecast"]')
            if forecast_section:
                forecast_text = forecast_section.get_text(strip=True)[:300]
                items.append({
                    'title': f"Forecast: {forecast_text[:80]}",
                    'url': url,
                    'date_text': datetime.now().strftime('%Y-%m-%d'),
                    'condition': forecast_text,
                    'is_forecast': True,
                    'type': 'forecast',
                })
        
        return items
    
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and parse weather HTML page."""
        try:
            headers = self._get_headers()
            resp = self.session.get(self.base_url, headers=headers, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            items = self._extract_weather_data(soup, resp.url)
            
            logger.info(f"Fetched {len(items)} weather items from {self.base_url}")
            return items
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {self.base_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {self.base_url}: {e}", exc_info=True)
            return []
    
    def normalize(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize weather item to common shape."""
        title = raw_item.get('title', '').strip()
        url = raw_item.get('url', '').strip()
        if not title:
            return None
        
        # Parse date if available
        event_date = None
        date_text = raw_item.get('date_text', '')
        if date_text:
            try:
                from dateutil import parser
                event_date = parser.parse(date_text, dayfirst=True, fuzzy=True)
            except Exception:
                # Try relative dates (e.g., "today", "tomorrow")
                today = datetime.now()
                if 'today' in date_text.lower():
                    event_date = today
                elif 'tomorrow' in date_text.lower():
                    event_date = today + timedelta(days=1)
                else:
                    event_date = today  # Default to today for forecasts
        
        # Use event_date for forecasts, published_at for reports
        if raw_item.get('is_forecast'):
            # Forecasts have future dates
            published_at = None
        else:
            # Reports are current/past
            published_at = datetime.now()
        
        return {
            'source_name': self.source_name,
            'title': title,
            'url': url or self.base_url,
            'published_at': published_at,
            'event_date': event_date,
            'location': None,  # Weather is generally regional
            'category': self.category,
            'raw_data': {
                'condition': raw_item.get('condition'),
                'temperature': raw_item.get('temperature'),
                'type': raw_item.get('type'),  # 'forecast', 'report', 'warning'
                'is_forecast': raw_item.get('is_forecast'),
            },
        }

