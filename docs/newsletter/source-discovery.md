# Source Discovery Documentation

## Overview

The source discovery process identifies Scottish weekly newspapers from Wikipedia and determines their technical accessibility for content harvesting.

## Discovery Script

**File**: `blog-core/newsletter/sources/discovery/scottish_newspapers.py`

### Usage

```bash
python blog-core/newsletter/sources/discovery/scottish_newspapers.py
```

### Process

1. **Wikipedia Parsing**: Fetches and parses the "Local weekly newspapers" section from Wikipedia
2. **RSS Feed Discovery**: Attempts to find RSS feeds using common patterns:
   - `/rss`
   - `/feed`
   - `/rss.xml`
   - `/feeds/all.rss`
3. **Article Listing Discovery**: Attempts to find article listing pages:
   - `/news`
   - `/local-news`
   - `/community`
   - `/latest`
4. **Robots.txt Check**: Verifies robots.txt compliance
5. **Access Mode Detection**: Determines access mode:
   - `rss_only`: RSS feed available
   - `html_list_only`: Only HTML listing pages available
   - `api`: API access available
   - `blocked`: Robots.txt blocks access

### Output

Results are saved to `data/scottish_newspaper_sources.json`:

```json
{
  "sources": [
    {
      "name": "Oban Times",
      "base_url": "https://www.obantimes.co.uk",
      "rss_url": "https://www.obantimes.co.uk/rss",
      "listing_url": "https://www.obantimes.co.uk/news",
      "access_mode": "rss_only",
      "region": "Argyll",
      "robots_allowed": true,
      "discovery_notes": "RSS feed found at /rss"
    }
  ]
}
```

## Source Configuration

### Database Fields

After discovery, sources are inserted into `newsletter_snapshot_source` with:

- `name`: Newspaper name
- `base_url`: Base URL
- `type`: `rss` or `html`
- `region`: Geographic region (e.g., "Argyll", "Highlands")
- `preferred_sections`: Array of preferred sections (e.g., `['community', 'lifestyle']`)
- `excluded_sections`: Array of excluded sections (e.g., `['crime', 'court']`)
- `access_mode`: `rss_only`, `html_list_only`, `api`, or `blocked`
- `discovery_notes`: Notes from discovery process
- `enabled`: `false` initially (enable after testing)

### Seeding Sources

After discovery, run the seed script to insert sources:

```bash
python -c "
import json
from blog_core.newsletter.db.queries_sources import store_source

with open('data/scottish_newspaper_sources.json') as f:
    data = json.load(f)
    for source in data['sources']:
        store_source(
            name=source['name'],
            base_url=source.get('rss_url') or source.get('listing_url') or source['base_url'],
            source_type=source['access_mode'].split('_')[0],  # rss_only -> rss
            region=source.get('region'),
            preferred_sections=source.get('preferred_sections', []),
            excluded_sections=source.get('excluded_sections', []),
            access_mode=source['access_mode'],
            discovery_notes=source.get('discovery_notes'),
            enabled=False
        )
"
```

## Troubleshooting

### No RSS Feeds Found

- Check if newspaper uses different RSS feed patterns
- Verify website structure hasn't changed
- Consider using HTML listing pages instead

### Robots.txt Blocks Access

- Check robots.txt manually: `https://example.com/robots.txt`
- Verify user-agent is allowed
- May need to contact website owner for permission

### Access Mode Detection Fails

- Manually verify RSS feed URLs
- Test HTML listing pages in browser
- Update discovery script with site-specific patterns

### Source Not Appearing in UI

- Verify source was inserted into database
- Check `enabled` field is set to `true` (after testing)
- Verify source appears in `/newsletter/sources` endpoint

## Best Practices

1. **Test Before Enabling**: Always test sources with `enabled=false` first
2. **Monitor Access**: Regularly check if sources are still accessible
3. **Respect Rate Limits**: Don't fetch too frequently (default: 4 hours)
4. **Handle Errors Gracefully**: Sources may go offline or change structure
5. **Update Discovery Notes**: Document any manual configuration needed

