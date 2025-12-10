"""
Channel Content Format Configuration
Defines format-specific configurations for (channel, content_format) combinations.

This enables different formatting rules, templates, and requirements
for different content formats within the same channel.

For example:
- Facebook + recipe: Recipe-specific Facebook post format
- Facebook + word_of_day: Word of the Day Facebook post format
- Instagram + word_of_day: Word of the Day Instagram format
"""

# Format-specific configurations
# Format: (channel, content_format) -> {config}
CHANNEL_CONTENT_FORMATS = {
    # Blog formats
    ('blog', 'article'): {
        'template': 'blog/article.html',
        'requires_post': True,
        'sections': ['introduction', 'body', 'conclusion'],
        'required_fields': ['title', 'standfirst', 'body']
    },
    ('blog', 'recipe'): {
        'template': 'blog/recipe.html',
        'requires_post': True,
        'sections': ['introduction', 'ingredients', 'method', 'notes'],
        'required_fields': ['title', 'ingredients', 'method']
    },
    ('blog', 'profile'): {
        'template': 'blog/profile.html',
        'requires_post': True,
        'sections': ['introduction', 'body', 'gallery', 'explore_links'],
        'required_fields': ['title', 'standfirst', 'body']
    },
    ('blog', 'word_of_day'): {
        'template': 'blog/word_of_day.html',
        'requires_post': False,  # Words don't go to blog
        'sections': [],
        'required_fields': []
    },
    ('blog', 'phrase_of_day'): {
        'template': 'blog/phrase_of_day.html',
        'requires_post': False,  # Phrases don't go to blog
        'sections': [],
        'required_fields': []
    },
    ('blog', 'insult_of_day'): {
        'template': 'blog/insult_of_day.html',
        'requires_post': False,  # Insults don't go to blog
        'sections': [],
        'required_fields': []
    },
    
    # Facebook formats
    ('facebook', 'recipe'): {
        'template': 'facebook/recipe.html',
        'requires_post': False,  # Can be standalone Facebook post
        'max_length': 2000,
        'requires_image': True,
        'format_function': 'format_recipe_for_facebook',
        'hashtags': ['#ScottishRecipes', '#ClanRecipes']
    },
    ('facebook', 'word_of_day'): {
        'template': 'facebook/word_of_day.html',
        'requires_post': False,
        'max_length': 500,
        'requires_image': True,
        'format_function': 'format_word_for_facebook',
        'hashtags': ['#ScotsWord', '#ScottishLanguage']
    },
    ('facebook', 'phrase_of_day'): {
        'template': 'facebook/phrase_of_day.html',
        'requires_post': False,
        'max_length': 500,
        'requires_image': True,
        'format_function': 'format_phrase_for_facebook',
        'hashtags': ['#ScotsPhrase', '#ScottishLanguage']
    },
    ('facebook', 'insult_of_day'): {
        'template': 'facebook/insult_of_day.html',
        'requires_post': False,
        'max_length': 500,
        'requires_image': True,
        'format_function': 'format_insult_for_facebook',
        'hashtags': ['#ScotsInsult', '#ScottishLanguage']
    },
    ('facebook', 'syndication'): {
        'template': 'facebook/syndication.html',
        'requires_post': True,  # Must have blog post to syndicate
        'max_length': 2000,
        'requires_image': False,  # Uses blog post image
        'format_function': 'format_syndication_for_facebook',
        'hashtags': []
    },
    ('facebook', 'product'): {
        'template': 'facebook/product.html',
        'requires_post': False,
        'max_length': 2000,
        'requires_image': True,
        'format_function': 'format_product_for_facebook',
        'hashtags': []
    },
    
    # Instagram formats
    ('instagram', 'word_of_day'): {
        'template': 'instagram/word_of_day.html',
        'requires_post': False,
        'max_caption_length': 2200,
        'requires_image': True,
        'format_function': 'format_word_for_instagram',
        'hashtags': ['#ScotsWord', '#ScottishLanguage', '#ClanCom']
    },
    ('instagram', 'phrase_of_day'): {
        'template': 'instagram/phrase_of_day.html',
        'requires_post': False,
        'max_caption_length': 2200,
        'requires_image': True,
        'format_function': 'format_phrase_for_instagram',
        'hashtags': ['#ScotsPhrase', '#ScottishLanguage', '#ClanCom']
    },
    ('instagram', 'insult_of_day'): {
        'template': 'instagram/insult_of_day.html',
        'requires_post': False,
        'max_caption_length': 2200,
        'requires_image': True,
        'format_function': 'format_insult_for_instagram',
        'hashtags': ['#ScotsInsult', '#ScottishLanguage', '#ClanCom']
    },
    ('instagram', 'carousel'): {
        'template': 'instagram/carousel.html',
        'requires_post': True,
        'max_caption_length': 2200,
        'requires_image': True,
        'requires_multiple_images': True,
        'format_function': 'format_carousel_for_instagram',
        'hashtags': []
    },
    ('instagram', 'syndication'): {
        'template': 'instagram/syndication.html',
        'requires_post': True,
        'max_caption_length': 2200,
        'requires_image': True,
        'format_function': 'format_syndication_for_instagram',
        'hashtags': []
    },
    
    # Twitter formats
    ('twitter', 'word_of_day'): {
        'template': 'twitter/word_of_day.html',
        'requires_post': False,
        'max_length': 280,
        'requires_image': False,  # Optional for Twitter
        'format_function': 'format_word_for_twitter',
        'hashtags': ['#ScotsWord', '#ScottishLanguage']
    },
    ('twitter', 'phrase_of_day'): {
        'template': 'twitter/phrase_of_day.html',
        'requires_post': False,
        'max_length': 280,
        'requires_image': False,
        'format_function': 'format_phrase_for_twitter',
        'hashtags': ['#ScotsPhrase', '#ScottishLanguage']
    },
    ('twitter', 'insult_of_day'): {
        'template': 'twitter/insult_of_day.html',
        'requires_post': False,
        'max_length': 280,
        'requires_image': False,
        'format_function': 'format_insult_for_twitter',
        'hashtags': ['#ScotsInsult', '#ScottishLanguage']
    },
    ('twitter', 'syndication'): {
        'template': 'twitter/syndication.html',
        'requires_post': True,
        'max_length': 280,
        'requires_image': False,
        'format_function': 'format_syndication_for_twitter',
        'hashtags': []
    },
    
    # Newsletter formats
    ('newsletter', 'syndication'): {
        'template': 'newsletter/syndication.html',
        'requires_post': True,
        'format_function': 'format_syndication_for_newsletter',
        'sections': ['summary', 'link', 'image']
    },
    ('newsletter', 'roundup'): {
        'template': 'newsletter/roundup.html',
        'requires_post': False,
        'format_function': 'format_roundup_for_newsletter',
        'sections': ['items', 'links']
    }
}


def get_format_config(channel: str, content_format: str) -> dict:
    """
    Get configuration for a (channel, content_format) combination.
    
    Args:
        channel: Channel name ('blog', 'facebook', 'instagram', etc.)
        content_format: Content format ('recipe', 'word_of_day', 'syndication', etc.)
    
    Returns:
        dict: Format configuration, or empty dict if not found
    """
    key = (channel.lower(), content_format.lower())
    return CHANNEL_CONTENT_FORMATS.get(key, {})


def requires_post(channel: str, content_format: str) -> bool:
    """
    Check if a format requires a blog post to exist.
    
    Args:
        channel: Channel name
        content_format: Content format
    
    Returns:
        bool: True if format requires a post, False otherwise
    """
    config = get_format_config(channel, content_format)
    return config.get('requires_post', False)


def get_format_function(channel: str, content_format: str) -> str:
    """
    Get the format function name for a (channel, content_format) combination.
    
    Args:
        channel: Channel name
        content_format: Content format
    
    Returns:
        str: Function name, or None if not found
    """
    config = get_format_config(channel, content_format)
    return config.get('format_function')


def get_max_length(channel: str, content_format: str) -> int:
    """
    Get maximum content length for a format.
    
    Args:
        channel: Channel name
        content_format: Content format
    
    Returns:
        int: Maximum length, or None if not specified
    """
    config = get_format_config(channel, content_format)
    # Handle different length field names
    return config.get('max_length') or config.get('max_caption_length')


def get_hashtags(channel: str, content_format: str) -> list:
    """
    Get default hashtags for a format.
    
    Args:
        channel: Channel name
        content_format: Content format
    
    Returns:
        list: List of hashtags, or empty list if not specified
    """
    config = get_format_config(channel, content_format)
    return config.get('hashtags', [])

