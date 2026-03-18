# Recipe Section Types

This document defines the section types used in Scottish Recipe posts.

## Recipe Post Sections

### `recipe_background`
**Purpose:** Historic/cultural background  
**Content:** 2-3 paragraphs (150-200 words) covering origin story, regional associations, occasions when traditionally eaten  
**Display:** Text content with optional cultural/historic context image  
**Voice:** Warm, storytelling, evoking place, people, and time. Not academic - written for curiosity and engagement.

### `recipe_ingredients`
**Purpose:** Ingredients list  
**Content:** Clear, readable ingredients list formatted for home cooks  
**Display:** Formatted list with clear typography  
**Notes:** May include regional variations or historical notes

### `recipe_method`
**Purpose:** Recipe method/steps  
**Content:** Numbered steps with clear instructions  
**Display:** Numbered list with clear step-by-step formatting  
**Notes:** Aimed at home cooks, not professional chefs

### `recipe_variants`
**Purpose:** Optional twists and variations  
**Content:** 1-2 optional twists (e.g., "Hebridean version uses smoked haddock only", "Modern twist: add whisky cream")  
**Display:** Text content, optional  
**Notes:** Not every recipe needs variants - this section is optional

### `recipe_serving`
**Purpose:** Serving suggestions and accompaniments  
**Content:** "How Scots serve it" section: drinks, sides, or traditional accompaniments  
**Display:** Text content  
**Notes:** Optional mention of related products available on clan.com

### `recipe_further_reading`
**Purpose:** Authoritative sources for background information  
**Content:** 2-5 authoritative sources with: Title & Link, Why It's Good, and Use Case in Your Content  
**Display:** Formatted list of sources with links and explanatory notes  
**Storage:** Text content in `post_section.polished` or `post_section.draft`  
**Notes:** 
- Focus on: cultural/heritage sites, Wikipedia articles, historical sources, ingredient provenance sites, tourism/heritage organizations
- AVOID: competing recipe sites or cooking blogs
- Each source should include:
  - Title & Link
  - Why It's Good (brief explanation of the source's value)
  - Use Case in Your Content (how to reference this source in other recipe sections)
- Sources should support the Background, Ingredients, Variations, and Serving Suggestions sections

## Section Storage

Sections are stored in the existing `post_section` table:
- `section_type` - One of the types above
- `section_heading` - Section title
- `polished` or `draft` - HTML content

### Ingredients Section
- Consider storing structured data in `post_section_elements` JSONB for future use:
  ```json
  {
    "ingredients": [
      {"amount": "500g", "item": "smoked haddock"},
      {"amount": "1", "item": "onion, finely chopped"}
    ],
    "serves": 4
  }
  ```
- Currently: Store as formatted HTML in `polished` field

### Method Section
- Store steps in `post_section_elements` JSONB:
  ```json
  {
    "steps": [
      {"number": 1, "instruction": "Heat the butter in a large pan..."},
      {"number": 2, "instruction": "Add the onion and cook until soft..."}
    ]
  }
  ```
- Currently: Store as numbered HTML list in `polished` field

## Section Order

Standard recipe post section order:
1. `recipe_background` - Historic/cultural context
2. `recipe_ingredients` - Ingredients list
3. `recipe_method` - Recipe steps
4. `recipe_variants` - Optional variations (if applicable)
5. `recipe_serving` - Serving suggestions
6. `recipe_further_reading` - Authoritative sources for background

## Integration with Existing System

- Recipe sections use the same `post_section` table as profile sections
- Section types are distinguished by `section_type` field value
- Workflow system can process recipe sections using standard section workflow
- LLM prompts can target specific recipe section types
- Images use existing `post_images` linking system

