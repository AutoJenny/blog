# Recipe Section Structured Formats

This document defines the strict JSON formats for each recipe section type.

## Overview

Recipe sections use structured JSON stored in `post_section_elements` (JSONB column) to ensure consistent formatting and enable proper rendering.

## Section Formats

### `recipe_background`
**Format:** Plain text (HTML in `draft`/`polished` fields)
**JSON Structure:** Not required - this section uses standard HTML content

### `recipe_ingredients`
**Format:** Structured list with weights in both imperial and metric
**JSON Structure:**
```json
{
  "serves": 4,
  "prep_time": "15 minutes",
  "cook_time": "30 minutes",
  "ingredients": [
    {
      "item": "smoked haddock",
      "amount_imperial": "500g",
      "amount_metric": "500g",
      "notes": "undyed, skinless"
    },
    {
      "item": "onion",
      "amount_imperial": "1 large",
      "amount_metric": "1 large",
      "notes": "finely chopped"
    },
    {
      "item": "potatoes",
      "amount_imperial": "300g",
      "amount_metric": "300g",
      "notes": "peeled and diced"
    }
  ]
}
```

**Ordering Rules:**
- Ingredients must be listed in **weight order** (heaviest first)
- If no weight specified, use alphabetical order
- Convert all weights to grams for sorting
- Display with both imperial and metric

### `recipe_method`
**Format:** Numbered steps
**JSON Structure:**
```json
{
  "steps": [
    {
      "number": 1,
      "instruction": "Heat the butter in a large pan over medium heat.",
      "time": "2 minutes",
      "temperature": null
    },
    {
      "number": 2,
      "instruction": "Add the onion and cook until soft and translucent.",
      "time": "5 minutes",
      "temperature": "medium"
    },
    {
      "number": 3,
      "instruction": "Add the haddock and cook for 5 minutes.",
      "time": "5 minutes",
      "temperature": "medium-low"
    }
  ]
}
```

### `recipe_variants`
**Format:** List of variations
**JSON Structure:**
```json
{
  "variants": [
    {
      "name": "Hebridean Version",
      "description": "Uses smoked haddock only, no other fish",
      "changes": [
        "Replace mixed fish with 600g smoked haddock only"
      ]
    },
    {
      "name": "Modern Twist",
      "description": "Add whisky cream for richness",
      "changes": [
        "Add 50ml single malt whisky",
        "Add 100ml double cream at the end"
      ]
    }
  ]
}
```

### `recipe_serving`
**Format:** Serving suggestions
**JSON Structure:**
```json
{
  "serving_suggestions": [
    {
      "type": "traditional",
      "description": "Serve hot with crusty bread and butter",
      "accompaniments": [
        "Crusty white bread",
        "Scottish butter"
      ]
    },
    {
      "type": "drinks",
      "description": "Pair with a light ale or whisky",
      "accompaniments": [
        "Belhaven Best",
        "Glenfiddich 12"
      ]
    }
  ],
  "related_products": [
    {
      "name": "Scottish Smoked Haddock",
      "url": "https://clan.com/products/smoked-haddock"
    }
  ]
}
```

### `recipe_further_reading`
**Format:** List of sources
**JSON Structure:**
```json
{
  "sources": [
    {
      "title": "Cullen Skink",
      "url": "https://en.wikipedia.org/wiki/Cullen_skink",
      "why_good": "Provides broad overview: origin in the town of Cullen, ingredients (smoked haddock, potatoes, onions), etymology of 'skink'.",
      "use_case": "Use in the 'Historic/cultural background' section as a general background link."
    },
    {
      "title": "Cullen Skink – The birthplace of Cullen Skink",
      "url": "https://discovercullen.com/cullen-skink",
      "why_good": "Local tourism/cultural site; discusses how the dish evolved from beef broth to fish in the 1890s in Cullen.",
      "use_case": "Good for regional provenance & story-tie to the town of Cullen; link here when you mention the place."
    }
  ]
}
```

## Storage

- Structured data stored in `post_section_elements` (JSONB column)
- HTML content stored in `post_section.draft` or `post_section.polished`
- Both can coexist - structured data for programmatic access, HTML for display

## Validation

Each section type should validate its JSON structure:
- Required fields must be present
- Data types must match specification
- Weight values must be parseable for sorting

