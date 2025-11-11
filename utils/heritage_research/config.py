"""
Configuration for Heritage Research System

Research frequency and other settings are configurable here.
"""

import os
from typing import Literal

# Research frequency modes
ResearchFrequency = Literal['on_demand', 'scheduled', 'interval']

# Current research frequency (configurable for future product profiling calendar)
RESEARCH_FREQUENCY: ResearchFrequency = 'on_demand'  # Can be changed to 'scheduled' or 'interval' in future

# Research dimensions
RESEARCH_DIMENSIONS = [
    'historical_origins',
    'cultural_significance',
    'evolution',
    'scottish_heritage_connections',
    'industrial_legacy'
]

# Wikipedia API settings
WIKIPEDIA_LANGUAGE = 'en'
WIKIPEDIA_MAX_RESULTS = 10

# Google Custom Search settings (free tier: 100 queries/day)
GOOGLE_SEARCH_ENABLED = os.getenv('GOOGLE_SEARCH_ENABLED', 'false').lower() == 'true'
GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY', '')
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')
GOOGLE_SEARCH_DAILY_LIMIT = 100
GOOGLE_SEARCH_CREDIBLE_DOMAINS = [
    'ac.uk',  # Academic
    'gov.uk',  # Government
    'nms.ac.uk',  # National Museum of Scotland
    'nls.uk',  # National Library of Scotland
    'historicenvironment.scot',  # Historic Environment Scotland
    'visitscotland.com',  # VisitScotland
]

# Source credibility scoring
CREDIBILITY_SCORES = {
    'museum': 1.0,
    'academic': 0.95,
    'government': 0.90,
    'wikipedia': 0.85,
    'established_media': 0.80,
    'specialist_site': 0.75,
    'other': 0.50
}

# Synthesis settings
SYNTHESIS_NARRATIVE_LENGTH = (300, 500)  # Word range
SYNTHESIS_MIN_SOURCES = 3  # Minimum sources per dimension

