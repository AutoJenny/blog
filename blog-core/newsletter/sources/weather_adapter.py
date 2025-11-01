"""Weather adapter for scraping weather reports and forecasts from HTML pages."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, date
from urllib.parse import urljoin, urlparse
import logging
import re
import json
from dateutil import parser
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
        
        # BBC Weather page structure
        if 'bbc.co.uk/weather' in url.lower():
            items = self._extract_bbc_weather(soup, url)
        
        # Met Office structure
        elif 'metoffice' in url.lower():
            items = self._extract_metoffice_weather(soup, url)
        
        return items
    
    def _extract_bbc_weather(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract daily forecasts from BBC Weather page."""
        items = []
        today = datetime.now()
        
        # First try JSON data (more reliable and structured)
        json_items = self._extract_bbc_json_data(soup, url)
        if json_items:
            return json_items
        
        # Fallback to HTML parsing if JSON fails
        # BBC uses .wr-day for daily forecasts (14-day forecast)
        day_elements = soup.select('.wr-day')
        
        for idx, day_elem in enumerate(day_elements[:14]):  # Up to 14 days
            try:
                # Extract date
                date_elem = day_elem.select_one('h2, h3, [class*="date"], [class*="day-name"]')
                date_text = ''
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                else:
                    # Calculate date from index
                    forecast_date = today + timedelta(days=idx)
                    if idx == 0:
                        date_text = 'Today'
                    elif idx == 1:
                        date_text = 'Tomorrow'
                    else:
                        date_text = forecast_date.strftime('%A %d %B')
                
                # Extract temperatures (high/low)
                temp_elements = day_elem.select('[class*="temp"], [class*="temperature"]')
                temp_text = ''
                temp_high = None
                temp_low = None
                
                for temp_elem in temp_elements:
                    temp_str = temp_elem.get_text(strip=True)
                    # Look for numbers with degree symbols
                    temp_match = re.search(r'(\d+)\s*°', temp_str)
                    if temp_match:
                        temp_val = int(temp_match.group(1))
                        if temp_high is None or temp_val > temp_high:
                            temp_high = temp_val
                        if temp_low is None or temp_val < temp_low:
                            temp_low = temp_val
                        temp_text = f"{temp_val}°C"
                
                # Extract condition/description
                desc_elem = day_elem.select_one('[class*="desc"], [class*="condition"], [class*="type"], [class*="summary"]')
                condition = desc_elem.get_text(strip=True) if desc_elem else ''
                
                # Extract precipitation
                precip_elem = day_elem.select_one('[class*="precip"], [class*="rain"], [class*="mm"]')
                precipitation = precip_elem.get_text(strip=True) if precip_elem else ''
                
                # Extract wind info
                wind_elem = day_elem.select_one('[class*="wind"]')
                wind = wind_elem.get_text(strip=True) if wind_elem else ''
                
                # Calculate forecast date
                forecast_date = today + timedelta(days=idx)
                
                # Build title
                title_parts = [date_text]
                if temp_text:
                    title_parts.append(temp_text)
                if condition:
                    title_parts.append(condition)
                title = ' - '.join(title_parts) or f"Weather forecast for {date_text}"
                
                items.append({
                    'title': title,
                    'url': url,
                    'date_text': date_text,
                    'forecast_date': forecast_date,
                    'day_index': idx,
                    'condition': condition,
                    'temperature': temp_text,
                    'temp_high': temp_high,
                    'temp_low': temp_low,
                    'precipitation': precipitation,
                    'wind': wind,
                    'is_forecast': idx >= 0,  # All are forecasts
                    'type': 'daily_forecast',
                })
            except Exception as e:
                logger.debug(f"Error extracting day {idx} from BBC weather: {e}")
                continue
        
        # Also extract current conditions if available
        current_elem = soup.select_one('[class*="current"], [class*="now"], [data-testid*="current"]')
        if current_elem:
            current_temp = ''
            temp_elem = current_elem.select_one('[class*="temp"]')
            if temp_elem:
                temp_match = re.search(r'(\d+)\s*°', temp_elem.get_text())
                if temp_match:
                    current_temp = f"{temp_match.group(1)}°C"
            
            current_condition = current_elem.get_text(strip=True)[:100]
            if current_temp or current_condition:
                items.insert(0, {
                    'title': f"Current: {current_temp} {current_condition}" if current_temp else f"Current conditions: {current_condition}",
                    'url': url,
                    'date_text': 'Today',
                    'forecast_date': today,
                    'day_index': -1,  # Current, not forecast
                    'condition': current_condition,
                    'temperature': current_temp,
                    'is_forecast': False,
                    'type': 'current',
                })
        
        return items
    
    def _extract_bbc_json_data(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract weather data from JSON in script tags (primary method - more reliable)."""
        items = []
        
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'data' in data:
                    data_obj = data.get('data', {})
                    forecasts = data_obj.get('forecasts', [])
                    
                    if isinstance(forecasts, list) and len(forecasts) > 0:
                        today = datetime.now()
                        
                        for idx, forecast in enumerate(forecasts):
                            try:
                                # Each forecast has 'detailed' and 'summary' keys
                                detailed = forecast.get('detailed', {})
                                summary = forecast.get('summary', {})
                                
                                # Calculate forecast date from day index (idx 0 = today, 1 = tomorrow, etc.)
                                # Always use day_index calculation to ensure correct future dates
                                forecast_date = today + timedelta(days=idx)
                                # Convert to date object (not datetime) for event_date
                                forecast_date = forecast_date.date()
                                
                                # Extract temperature data
                                reports = detailed.get('reports', [])
                                temp_high = None
                                temp_low = None
                                condition = ''
                                feels_like = None
                                
                                if reports:
                                    # Get max/min temps from reports
                                    temps = []
                                    conditions = []
                                    for report in reports:
                                        if 'maxTempC' in report:
                                            temps.append(report['maxTempC'])
                                        if 'minTempC' in report:
                                            temps.append(report['minTempC'])
                                        if 'temperatureC' in report:
                                            temps.append(report['temperatureC'])
                                        if 'enhancedWeatherDescription' in report:
                                            conditions.append(report['enhancedWeatherDescription'])
                                        if 'feelsLikeTemperatureC' in report:
                                            feels_like = report['feelsLikeTemperatureC']
                                    
                                    if temps:
                                        temp_high = max(temps)
                                        temp_low = min(temps)
                                    
                                    if conditions:
                                        condition = conditions[0]
                                
                                # Fallback to summary if detailed missing
                                if not condition and 'weatherType' in summary:
                                    condition = summary['weatherType']
                                
                                if not temp_high and 'maxTemp' in summary:
                                    temp_high = summary['maxTemp']
                                if not temp_low and 'minTemp' in summary:
                                    temp_low = summary['minTemp']
                                
                                # Build title
                                date_text = 'Today' if idx == 0 else ('Tomorrow' if idx == 1 else forecast_date.strftime('%A %d %B'))
                                title_parts = [date_text]
                                if temp_high is not None and temp_low is not None:
                                    title_parts.append(f"High {temp_high}°C / Low {temp_low}°C")
                                elif temp_high is not None:
                                    title_parts.append(f"{temp_high}°C")
                                if condition:
                                    title_parts.append(condition)
                                
                                items.append({
                                    'title': ' - '.join(title_parts),
                                    'url': url,
                                    'date_text': date_text,
                                    'forecast_date': forecast_date,
                                    'day_index': idx,
                                    'condition': condition,
                                    'temperature': f"{temp_high}°C / {temp_low}°C" if (temp_high is not None and temp_low is not None) else (f"{temp_high}°C" if temp_high else ''),
                                    'temp_high': temp_high,
                                    'temp_low': temp_low,
                                    'feels_like': feels_like,
                                    'precipitation': detailed.get('precipitationProbability', ''),
                                    'wind': f"{detailed.get('windSpeedMph', '')}mph" if detailed.get('windSpeedMph') else '',
                                    'is_forecast': idx >= 0,
                                    'type': 'daily_forecast',
                                    'raw_forecast': forecast,  # Store full data
                                })
                            except Exception as e:
                                logger.debug(f"Error parsing forecast {idx}: {e}")
                                continue
                        
                        break  # Found forecasts, exit loop
            except Exception as e:
                logger.debug(f"Error parsing JSON script: {e}")
                continue
        
        return items
    
    def _extract_metoffice_weather(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract weather data from Met Office HTML page."""
        items = []
        
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
        
        # Use forecast_date if available (from BBC JSON extraction)
        if raw_item.get('forecast_date'):
            forecast_date_val = raw_item['forecast_date']
            if isinstance(forecast_date_val, datetime):
                event_date = forecast_date_val
            elif isinstance(forecast_date_val, date):
                # Convert date to datetime at midnight
                event_date = datetime.combine(forecast_date_val, datetime.min.time())
            elif isinstance(forecast_date_val, str):
                try:
                    event_date = parser.parse(forecast_date_val)
                except:
                    event_date = None
            else:
                event_date = forecast_date_val
        elif not event_date and raw_item.get('day_index') is not None:
            # Calculate from day_index
            today = datetime.now()
            day_index = raw_item['day_index']
            if day_index >= 0:  # Future forecast
                event_date = today + timedelta(days=day_index)
                event_date = event_date.replace(hour=0, minute=0, second=0, microsecond=0)
            else:  # Current/past (day_index -1 or negative)
                event_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return {
            'source_name': self.source_name,
            'title': title,
            'url': url or self.base_url,
            'published_at': published_at,
            'event_date': event_date,
            'location': raw_item.get('location'),  # Can specify region
            'category': self.category,
            'raw_data': {
                'condition': raw_item.get('condition'),
                'temperature': raw_item.get('temperature'),
                'temp_high': raw_item.get('temp_high'),
                'temp_low': raw_item.get('temp_low'),
                'feels_like': raw_item.get('feels_like'),
                'precipitation': raw_item.get('precipitation'),
                'wind': raw_item.get('wind'),
                'type': raw_item.get('type'),  # 'daily_forecast', 'current', 'warning'
                'is_forecast': raw_item.get('is_forecast'),
                'day_index': raw_item.get('day_index'),
                'raw_forecast': raw_item.get('raw_forecast'),  # Full JSON data if from BBC
            },
        }

