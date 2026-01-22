"""
Research Topics Configuration
Defines research topics per post type for the background research system.

Each post type can have different research topics with different search strategies,
source priorities, and focus areas. This configuration drives the automatic
initialization of research topics when a post enters the research stage.
"""

RESEARCH_TOPICS_CONFIG = {
    'recipe': {
        'topics': [
            {
                'key': 'origins',
                'label': 'Origins & Early History',
                'search_template': '{item_name} history origins Scotland',
                'search_variations': [
                    '{item_name} history and origins',
                    '{item_name} earliest mentions Scotland',
                    '{item_name} historical background',
                    '{item_name} origin story Scotland',
                    'history of {item_name} Scottish food'
                ],
                'focus_areas': [
                    'first documented appearance',
                    'original location/region',
                    'earliest written records',
                    'historical cookbook references',
                    'creator or inventor (if known)',
                    'original purpose or context',
                    'specific dates and years',
                    'specific people and names',
                    'specific locations and places',
                    'literary or historical references'
                ],
                'source_priorities': ['academic', 'museum', 'heritage', 'news', 'cultural'],
                'word_target': 200,
                'description': 'Research the earliest documented history and origins of this recipe in Scotland'
            },
            {
                'key': 'geographic_spread',
                'label': 'Geographic Spread & Regional Variations',
                'search_template': 'geographic distribution and regional variations of {item_name} across Scotland',
                'focus_areas': [
                    'regional variations',
                    'different names by region',
                    'local adaptations',
                    'regional popularity',
                    'specific towns or areas associated',
                    'regional differences in ingredients or method'
                ],
                'source_priorities': ['heritage', 'tourism', 'regional_history'],
                'word_target': 150,
                'description': 'Research how this recipe varies across different regions of Scotland'
            },
            {
                'key': 'evolution',
                'label': 'Evolution Over Time',
                'search_template': 'how {item_name} has evolved from historical to modern versions in Scotland',
                'focus_areas': [
                    'ingredient changes over time',
                    'cooking method evolution',
                    'when changes occurred',
                    'modern vs traditional versions',
                    'historical recipe comparisons',
                    'technological influences'
                ],
                'source_priorities': ['food_history', 'academic', 'museum'],
                'word_target': 150,
                'description': 'Research how this recipe has changed from its original form to modern versions'
            },
            {
                'key': 'cultural_significance',
                'label': 'Cultural Significance & Traditions',
                'search_template': 'cultural significance and traditional occasions for {item_name} in Scottish culture',
                'focus_areas': [
                    'traditional occasions when eaten',
                    'festival associations',
                    'cultural meaning',
                    'ceremonial use',
                    'social context',
                    'seasonal associations'
                ],
                'source_priorities': ['cultural_heritage', 'festival_orgs', 'tourism'],
                'word_target': 150,
                'description': 'Research the cultural and traditional significance of this recipe in Scotland'
            },
            {
                'key': 'modern_incarnations',
                'label': 'Modern Incarnations & Contemporary Use',
                'search_template': 'modern versions and contemporary uses of {item_name} in Scotland today',
                'focus_areas': [
                    'contemporary preparation methods',
                    'restaurant adaptations',
                    'home cooking trends',
                    'modern variations',
                    'current popularity',
                    'commercial availability'
                ],
                'source_priorities': ['contemporary_food', 'restaurant_reviews', 'modern_cookbooks'],
                'word_target': 100,
                'description': 'Research how this recipe is used and adapted in modern Scotland'
            }
        ]
    },
    'themed': {
        'topics': [
            {
                'key': 'historical_context',
                'label': 'Historical Context',
                'search_template': 'historical context and background of {item_name} in Scotland',
                'focus_areas': [
                    'historical period',
                    'key historical events',
                    'social and political context',
                    'historical significance'
                ],
                'source_priorities': ['academic', 'museum', 'heritage'],
                'word_target': 200,
                'description': 'Research the historical background and context of this theme'
            },
            {
                'key': 'cultural_significance',
                'label': 'Cultural Significance',
                'search_template': 'cultural significance of {item_name} in Scottish culture',
                'focus_areas': [
                    'cultural meaning',
                    'traditions and customs',
                    'symbolic importance',
                    'cultural practices'
                ],
                'source_priorities': ['cultural_heritage', 'academic', 'tourism'],
                'word_target': 200,
                'description': 'Research the cultural significance and meaning of this theme'
            },
            {
                'key': 'key_figures',
                'label': 'Key Figures & Events',
                'search_template': 'key figures and important events related to {item_name} in Scotland',
                'focus_areas': [
                    'notable people',
                    'important events',
                    'historical milestones',
                    'significant contributions'
                ],
                'source_priorities': ['academic', 'museum', 'heritage'],
                'word_target': 200,
                'description': 'Research key historical figures and events related to this theme'
            }
        ]
    },
    'profile': {
        'topics': [
            {
                'key': 'family_history',
                'label': 'Family History & Origins',
                'search_template': 'history and origins of {item_name} family in Scotland',
                'focus_areas': [
                    'earliest records',
                    'name origin',
                    'historical significance',
                    'clan associations'
                ],
                'source_priorities': ['academic', 'genealogy', 'heritage'],
                'word_target': 200,
                'description': 'Research the history and origins of this family in Scotland'
            },
            {
                'key': 'geographic_origins',
                'label': 'Geographic Origins & Distribution',
                'search_template': 'geographic origins and distribution of {item_name} surname in Scotland',
                'focus_areas': [
                    'original location',
                    'geographic distribution',
                    'regional concentrations',
                    'migration patterns'
                ],
                'source_priorities': ['genealogy', 'heritage', 'academic'],
                'word_target': 150,
                'description': 'Research the geographic origins and distribution of this family'
            },
            {
                'key': 'notable_members',
                'label': 'Notable Family Members',
                'search_template': 'notable members and achievements of {item_name} family in Scotland',
                'focus_areas': [
                    'famous individuals',
                    'historical achievements',
                    'contributions to Scotland',
                    'notable accomplishments'
                ],
                'source_priorities': ['academic', 'museum', 'heritage'],
                'word_target': 200,
                'description': 'Research notable members and achievements of this family'
            }
        ]
    }
}


def get_research_topics_for_post_type(post_type):
    """
    Get research topics for a specific post type.
    
    Args:
        post_type (str): Post type ('recipe', 'themed', 'profile', etc.)
    
    Returns:
        list: List of research topic configurations, or empty list if post type not found
    """
    if post_type not in RESEARCH_TOPICS_CONFIG:
        return []
    
    return RESEARCH_TOPICS_CONFIG[post_type]['topics']


def get_research_topic_by_key(post_type, topic_key):
    """
    Get a specific research topic by key for a post type.
    
    Args:
        post_type (str): Post type
        topic_key (str): Topic key (e.g., 'origins', 'geographic_spread')
    
    Returns:
        dict: Topic configuration, or None if not found
    """
    topics = get_research_topics_for_post_type(post_type)
    for topic in topics:
        if topic['key'] == topic_key:
            return topic
    return None


def has_research_topics(post_type):
    """
    Check if a post type has research topics configured.
    
    Args:
        post_type (str): Post type
    
    Returns:
        bool: True if post type has research topics, False otherwise
    """
    return post_type in RESEARCH_TOPICS_CONFIG and len(RESEARCH_TOPICS_CONFIG[post_type]['topics']) > 0
