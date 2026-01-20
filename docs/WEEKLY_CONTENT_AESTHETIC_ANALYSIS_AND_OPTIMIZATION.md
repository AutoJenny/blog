# Weekly Content Aesthetic Analysis and Optimization Algorithms

**Date:** 2026-01-20  
**Purpose:** Comprehensive aesthetic review of weekly content images and algorithms for optimizing presentation based on content length

---

## Part 1: Aesthetic Review of Current Post Types

### Current Issues (Common to All Types)

1. **Main Scots text too large** - 72pt font dominates, overwhelming other elements
2. **Excessive space after title** - Large gap between header and main content creates disconnected feel
3. **Cramped spacing to translation** - Insufficient space between main text and translation
4. **Supporting text too small** - Examples, notes, and translations feel diminutive

### Weekly Word (Current: "scunner")

**Aesthetic Problems:**
- Single word "scunner" at 72pt is disproportionately large
- Large empty space above word after title
- Translation "disgust; annoyance" cramped below main word
- Usage examples (36pt) too small relative to main word
- Overall vertical balance is top-heavy with compression below

### Weekly Phrase (Current: "Keep yersel tae yersel")

**Aesthetic Problems:**
- Phrase spans 2 lines at 72pt, still too large
- Very large gap between title and phrase
- Translation line very close to bottom of phrase ("yersel")
- Contextual note too small
- Uneven vertical distribution

### Weekly Insult (Current: "Ye're as useful as a chocolate fireguard")

**Aesthetic Problems:**
- Phrase spans 3 lines at 72pt, dominating image
- Excessive space above after title
- Translation cramped directly below "fireguard"
- Contextual text very small and partially truncated
- Visual hierarchy unbalanced

---

## Part 2: Aesthetic Review of Minimalist/Maximalist Examples

### Weekly Word - Minimalist ("wee")

**Observations:**
- Single short word "wee" at 72pt creates massive visual weight
- Extremely large empty space above after title
- Translation "small" positioned very close to word, overlapping decorative strokes
- Example phrases cramped and overlapping main word
- Supporting text lost in visual hierarchy

**Length:** 3 characters

### Weekly Word - Maximalist ("scunner")

**Observations:**
- Single longer word "scunner" at 72pt still too large
- Same spacing issues as minimalist
- Translation longer ("disgust; annoyance; strong dislike") but still cramped
- Three usage examples feel too small
- Notes text very long but tiny

**Length:** 7 characters

### Weekly Phrase - Minimalist ("Aye")

**Observations:**
- Single word "Aye" at 72pt, extremely large
- Massive empty space above
- Translation "Yes" positioned close to word
- Context "Universal Scots" cramped below
- Bottom section has excessive empty space

**Length:** 3 characters

### Weekly Phrase - Maximalist ("Keep yersel tae yersel")

**Observations:**
- Phrase spans 2 lines at 72pt
- Large gap after title
- Translation line cramped below
- Contextual note small
- Better balance than minimalist but still issues

**Length:** 24 characters

### Weekly Insult - Minimalist ("Eejit")

**Observations:**
- Single word "Eejit" at 72pt, overwhelming
- Large space above after title
- Translation "→ Idiot" very close below
- Description "Common Scots insult" too small
- Bottom section empty

**Length:** 5 characters

### Weekly Insult - Maximalist ("Ye're as useful as a chocolate fireguard")

**Observations:**
- Phrase spans 3 lines at 72pt
- Large gap after title
- Translation cramped below
- Contextual text very small and truncated
- Better use of vertical space than minimalist

**Length:** 42 characters

---

## Part 3: Optimization Algorithms

### Algorithm 1: Weekly Word Optimization

**Input Variables:**
- `scots_length`: Character count of Scots word
- `translation_length`: Character count of translation
- `num_examples`: Number of usage examples (0-3)
- `notes_length`: Character count of notes

**Font Size Algorithm:**
```python
# Base font size scales inversely with word length
if scots_length <= 3:
    scots_font_size = 64  # Smaller for very short words
elif scots_length <= 5:
    scots_font_size = 60
elif scots_length <= 7:
    scots_font_size = 56
else:
    scots_font_size = 52  # Longer words get smaller font

# Translation font size based on its length
if translation_length <= 10:
    translation_font_size = 38
elif translation_length <= 20:
    translation_font_size = 36
else:
    translation_font_size = 34

# Usage examples scale with number
if num_examples == 0:
    usage_font_size = 0
elif num_examples == 1:
    usage_font_size = 40
elif num_examples == 2:
    usage_font_size = 38
else:
    usage_font_size = 36
```

**Spacing Algorithm:**
```python
# Header to Scots spacing - tighter for shorter words
if scots_length <= 3:
    header_to_scots = 20  # Minimal spacing
elif scots_length <= 5:
    header_to_scots = 25
else:
    header_to_scots = 30

# Scots to translation spacing - increases with word length
base_scots_to_translation = 100
if scots_length <= 3:
    scots_to_translation = base_scots_to_translation + 40  # Extra space for short words
elif scots_length <= 5:
    scots_to_translation = base_scots_to_translation + 30
elif scots_length <= 7:
    scots_to_translation = base_scots_to_translation + 20
else:
    scots_to_translation = base_scots_to_translation + 10

# Translation to examples spacing
translation_to_examples = 60 + (num_examples * 5)  # More examples = more space
```

**Vertical Positioning Algorithm:**
```python
# Calculate total content height
total_content_height = (
    scots_height +
    scots_to_translation +
    translation_height +
    (translation_to_examples if num_examples > 0 else 0) +
    total_examples_height +
    examples_to_notes +
    notes_height
)

# Position Scots text - higher for shorter words
available_height = footer_top - header_bottom
if scots_length <= 3:
    # Short words: position higher, less centering
    scots_y = header_bottom + header_to_scots
elif scots_length <= 5:
    scots_y = header_bottom + header_to_scots + 10
else:
    # Longer words: more centered
    scots_y = header_bottom + (available_height - total_content_height) / 2
```

---

### Algorithm 2: Weekly Phrase Optimization

**Input Variables:**
- `scots_length`: Character count of Scots phrase
- `scots_lines`: Number of lines after wrapping
- `translation_length`: Character count of translation
- `notes_length`: Character count of notes

**Font Size Algorithm:**
```python
# Font size decreases as phrase gets longer
if scots_length <= 5:
    scots_font_size = 68  # Single short word/phrase
elif scots_length <= 15:
    scots_font_size = 64  # Short phrase
elif scots_length <= 25:
    scots_font_size = 60  # Medium phrase
elif scots_length <= 35:
    scots_font_size = 56  # Long phrase
else:
    scots_font_size = 52  # Very long phrase

# Adjust based on number of lines
if scots_lines >= 3:
    scots_font_size -= 2  # Slightly smaller for multi-line

# Translation font size
translation_font_size = 38 if translation_length <= 30 else 36
```

**Spacing Algorithm:**
```python
# Header spacing - tighter for longer phrases
if scots_length <= 10:
    header_to_scots = 25
elif scots_length <= 20:
    header_to_scots = 20
else:
    header_to_scots = 15

# Scots to translation - increases with phrase length and lines
base_spacing = 120
if scots_lines == 1:
    scots_to_translation = base_spacing + 20
elif scots_lines == 2:
    scots_to_translation = base_spacing + 10
else:  # 3+ lines
    scots_to_translation = base_spacing

# Add descender buffer for last line
last_line = scots_lines[-1] if scots_lines else ""
has_descenders = any(c in last_line.lower() for c in ['g', 'j', 'p', 'q', 'y'])
if has_descenders:
    scots_to_translation += 30
```

**Vertical Positioning Algorithm:**
```python
# For phrases, center content more dynamically
available_height = footer_top - header_bottom
content_center_y = header_bottom + (available_height / 2)

# Start position - adjust based on total content height
scots_y = content_center_y - (total_content_height / 2)

# Ensure minimum spacing from header
min_scots_y = header_bottom + header_to_scots
if scots_y < min_scots_y:
    scots_y = min_scots_y
```

---

### Algorithm 3: Weekly Insult Optimization

**Input Variables:**
- `scots_length`: Character count of Scots insult
- `scots_lines`: Number of lines after wrapping
- `translation_length`: Character count of translation
- `notes_length`: Character count of notes

**Font Size Algorithm:**
```python
# Insults can be very long - scale more aggressively
if scots_length <= 5:
    scots_font_size = 66  # Single word insult
elif scots_length <= 15:
    scots_font_size = 62
elif scots_length <= 25:
    scots_font_size = 58
elif scots_length <= 35:
    scots_font_size = 54
else:
    scots_font_size = 50  # Very long insults

# Multi-line adjustment
if scots_lines >= 3:
    scots_font_size -= 3  # More reduction for long multi-line

# Translation
translation_font_size = 38
```

**Spacing Algorithm:**
```python
# Header spacing - minimal for insults (they're long)
header_to_scots = 15

# Scots to translation - critical spacing
base_spacing = 130
if scots_lines == 1:
    scots_to_translation = base_spacing + 30
elif scots_lines == 2:
    scots_to_translation = base_spacing + 20
else:  # 3+ lines
    scots_to_translation = base_spacing + 10

# Descender buffer
last_line = scots_lines[-1] if scots_lines else ""
has_descenders = any(c in last_line.lower() for c in ['g', 'j', 'p', 'q', 'y'])
if has_descenders:
    scots_to_translation += 40  # Larger buffer for insults
```

**Vertical Positioning Algorithm:**
```python
# Insults need careful vertical distribution
available_height = footer_top - header_bottom

# For long insults, start higher to fit everything
if scots_lines >= 3:
    # Multi-line: position higher, less centering
    scots_y = header_bottom + header_to_scots
else:
    # Shorter: can center more
    content_center_y = header_bottom + (available_height / 2)
    scots_y = content_center_y - (total_content_height / 2)
    min_scots_y = header_bottom + header_to_scots
    if scots_y < min_scots_y:
        scots_y = min_scots_y
```

---

## Part 4: Implementation Recommendations

### Key Principles

1. **Inverse Relationship**: Longer content → smaller fonts, shorter content → larger fonts (but with limits)
2. **Dynamic Spacing**: Spacing adjusts based on content length and number of lines
3. **Vertical Balance**: Shorter content positioned higher, longer content can be more centered
4. **Descender Awareness**: Always account for descenders in spacing calculations
5. **Minimum/Maximum Limits**: Set bounds to prevent extremes

### Font Size Ranges

- **Scots Text**: 50-68pt (was fixed 72pt)
- **Translation**: 34-38pt (was fixed 40pt)
- **Usage Examples**: 36-40pt (was fixed 36pt)
- **Notes**: 30-32pt (was fixed 32pt)

### Spacing Ranges

- **Header to Scots**: 15-30px (was fixed ~10px)
- **Scots to Translation**: 100-180px (was fixed 140px)
- **Translation to Examples**: 60-75px (was fixed 70px)
- **Examples to Notes**: 50-60px (was fixed 60px)

### Next Steps

1. Implement these algorithms in `weekly_content_image_renderer_v2.py`
2. Test with current week's content
3. Generate new aesthetic analysis images
4. Refine based on visual results
