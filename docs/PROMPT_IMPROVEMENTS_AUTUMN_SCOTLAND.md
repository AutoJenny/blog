# Prompt Improvements: Theme-Title Conditioned Prompts

## Current Issues

1. **Hardcoded Season**: Prompts were hardcoded for autumn, but need to work for ALL seasons and themes
2. **Theme Title Not Used**: The theme title (e.g., "Autumn Landscapes Today") isn't being used as the primary conditioning factor
3. **Vague Seasonal Terms**: Results are "vaguely seasonal" because the season/theme isn't being extracted and emphasized from the theme title
4. **No Landmark Requirement**: Doesn't explicitly require Scottish landmarks when contextually relevant

## Solution: Theme-Title Primary Conditioning

The theme title (provided in {theme_data}) should be the PRIMARY conditioning factor. The prompt should:
1. Extract season/theme keywords from the theme title (e.g., "Autumn" from "Autumn Landscapes Today", "Winter" from "Winter in the Highlands")
2. Make those extracted terms MANDATORY in the query
3. Work universally for all seasons and themes

## Recommended Improvements

### For "Image Prompts Generation (Photo-harvesting)"

#### System Prompt Changes:
- Make theme title the PRIMARY conditioning: "The theme title (provided in {theme_data}) is the PRIMARY conditioning factor"
- Extract season/theme from theme title: "Extract and emphasize the season/theme from the theme title"
- Make extracted terms mandatory: "Make them MANDATORY in the query"
- Require Scottish landmark names when contextually relevant
- Use theme-appropriate visual elements (autumn colors for autumn themes, snow for winter themes, etc.)

#### User Prompt Changes:
- Emphasize theme title as PRIMARY CONDITIONING with clear instructions
- Provide examples showing how different theme titles produce different queries:
  - "Autumn Landscapes Today" → "autumn Scotland, ..."
  - "Winter in the Highlands" → "winter Scotland, ..."
  - "Spring Gardens of Scotland" → "spring Scotland, ..."
- Structure: "[season/theme from title] Scotland, [landmark if relevant], [visual elements]"

### For "Image Concepts Generation (Photo-harvesting)"

#### Add Requirements:
- Concepts must explicitly mention the season/theme from the theme title
- Concepts should reference Scottish landmarks when relevant to section content
- Visual elements should match the theme (autumn colors for autumn themes, winter elements for winter themes, etc.)

