# Weekly Content Image Optimization - Parameters and Current State

**Date:** 2026-01-20  
**Purpose:** Document all parameters, algorithms, and current issues for expert guidance on optimizing weekly content image generation

---

## Problem Statement

We need to generate square 1080×1080px images for three types of weekly Scots language content:
- **Weekly Word**: Single Scots words with translation, usage examples, and notes
- **Weekly Phrase**: Scots phrases with translation and notes
- **Weekly Insult**: Scots insults with translation and notes

**Current Issue:** Short content (minimalist examples) produces "disastrous" results, while longer content is generally acceptable. The layout needs to adapt dynamically to content length while maintaining aesthetic balance.

---

## Canvas Specifications

- **Size**: 1080×1080 pixels (square)
- **Background**: Solid dark blue (#283C66 or similar)
- **Text Color**: Off-white/cream (#f5f1e8)
- **Header/Footer Color**: Light grey

---

## Current Font Size Parameters

### Base Font Sizes (Constants)
```python
HEADER_FONT_SIZE = 48pt
FOOTER_FONT_SIZE = 24pt
PROVENANCE_FONT_SIZE = 32pt
```

### Dynamic Font Sizes (Current Algorithm)

#### Weekly Word Algorithm:
```python
# Scots text font size based on word length
if scots_length <= 3:
    scots_font_size = 64pt
elif scots_length <= 5:
    scots_font_size = 60pt
elif scots_length <= 7:
    scots_font_size = 56pt
else:
    scots_font_size = 52pt

# Translation font size based on translation length
if translation_length <= 10:
    translation_font_size = 38pt
elif translation_length <= 20:
    translation_font_size = 36pt
else:
    translation_font_size = 34pt

# Usage examples font size based on number of examples
if num_examples == 0:
    usage_font_size = 0
elif num_examples == 1:
    usage_font_size = 40pt
elif num_examples == 2:
    usage_font_size = 38pt
else:
    usage_font_size = 36pt
```

#### Weekly Phrase Algorithm:
```python
# Scots text font size based on phrase length
if scots_length <= 5:
    scots_font_size = 68pt
elif scots_length <= 15:
    scots_font_size = 64pt
elif scots_length <= 25:
    scots_font_size = 60pt
elif scots_length <= 35:
    scots_font_size = 56pt
else:
    scots_font_size = 52pt

# Adjust for multi-line
if scots_lines >= 3:
    scots_font_size -= 2pt

# Translation
translation_font_size = 38pt if translation_length <= 30 else 36pt
usage_font_size = 36pt
```

#### Weekly Insult Algorithm:
```python
# Scots text font size based on insult length
if scots_length <= 5:
    scots_font_size = 66pt
elif scots_length <= 15:
    scots_font_size = 62pt
elif scots_length <= 25:
    scots_font_size = 58pt
elif scots_length <= 35:
    scots_font_size = 54pt
else:
    scots_font_size = 50pt

# Adjust for multi-line
if scots_lines >= 3:
    scots_font_size -= 3pt

translation_font_size = 38pt
usage_font_size = 36pt
```

---

## Current Spacing Parameters

### Base Spacing Constants
```python
TRANSLATION_TO_USAGE_SPACING = 70px
USAGE_LINE_SPACING = 55px
USAGE_TO_PROVENANCE_SPACING = 60px
LINE_HEIGHT_MULTIPLIER = 1.3
DESCENDER_BUFFER = 40px
```

### Dynamic Spacing (Current Algorithm)

#### Weekly Word Spacing:
```python
# Header to Scots spacing
if scots_length <= 3:
    header_to_scots = 20px
elif scots_length <= 5:
    header_to_scots = 25px
else:
    header_to_scots = 30px

# Scots to translation spacing
base_scots_to_translation = 100px
if scots_length <= 3:
    scots_to_translation = base_scots_to_translation + 40px  # = 140px
elif scots_length <= 5:
    scots_to_translation = base_scots_to_translation + 30px  # = 130px
elif scots_length <= 7:
    scots_to_translation = base_scots_to_translation + 20px  # = 120px
else:
    scots_to_translation = base_scots_to_translation + 10px  # = 110px

# Translation to examples
translation_to_examples = 60px + (num_examples * 5px)
```

#### Weekly Phrase Spacing:
```python
# Header to Scots spacing
if scots_length <= 10:
    header_to_scots = 25px
elif scots_length <= 20:
    header_to_scots = 20px
else:
    header_to_scots = 15px

# Scots to translation spacing
base_spacing = 120px
if scots_lines == 1:
    scots_to_translation = base_spacing + 20px  # = 140px
elif scots_lines == 2:
    scots_to_translation = base_spacing + 10px  # = 130px
else:  # 3+ lines
    scots_to_translation = base_spacing  # = 120px

# Add descender buffer
if has_descenders:
    scots_to_translation += 30px
```

#### Weekly Insult Spacing:
```python
header_to_scots = 15px

# Scots to translation spacing
base_spacing = 130px
if scots_lines == 1:
    scots_to_translation = base_spacing + 30px  # = 160px
elif scots_lines == 2:
    scots_to_translation = base_spacing + 20px  # = 150px
else:  # 3+ lines
    scots_to_translation = base_spacing + 10px  # = 140px

# Add descender buffer
if has_descenders:
    scots_to_translation += 40px
```

---

## Layout Calculation Process

### Step 1: Measure All Elements
1. Measure header height (using HEADER_FONT_SIZE = 48pt)
2. Measure Scots text height (using calculated scots_font_size, with wrapping at 800px max width)
3. Measure translation height (using calculated translation_font_size)
4. Measure usage examples heights (if any, using calculated usage_font_size)
5. Measure notes/provenance height (using PROVENANCE_FONT_SIZE = 32pt)
6. Measure footer height (using FOOTER_FONT_SIZE = 24pt)

### Step 2: Calculate Available Space
```python
TOP_MARGIN = 90px
BOTTOM_MARGIN = 90px

header_bottom = TOP_MARGIN + header_height + header_to_scots
footer_top = CANVAS_SIZE - BOTTOM_MARGIN - footer_height - 20px
available_height = footer_top - header_bottom
```

### Step 3: Calculate Total Content Height
```python
total_content_height = (
    scots_height +
    scots_to_translation +
    trans_height +
    (translation_to_examples if usage_examples else 0) +
    total_usage_height +
    (USAGE_TO_PROVENANCE_SPACING if notes else translation_to_examples if not usage_examples else 0) +
    provenance_height
)
```

### Step 4: Position Scots Text
```python
# Center content within available space
content_center_y = header_bottom + (available_height // 2)
scots_y = content_center_y - (total_content_height // 2)

# Ensure minimum spacing from header
if scots_y < header_bottom:
    scots_y = header_bottom
```

### Step 5: Position Subsequent Elements
```python
scots_bottom = scots_y + actual_scots_height
translation_y = scots_bottom + scots_to_translation
usage_start_y = translation_y + trans_height + translation_to_examples
provenance_y = usage_start_y + total_usage_height + USAGE_TO_PROVENANCE_SPACING
```

---

## Text Wrapping Parameters

- **Max Width for Scots Text**: 800px
- **Font**: Baskerville-Italic (serif, italic)
- **Line Height Multiplier**: 1.3
- **Wrapping Method**: Word-by-word, measuring actual rendered width using ImageMagick

---

## Current Issues

### Short Content Problems (Minimalist Examples)

1. **Weekly Word "wee" (3 characters)**:
   - Font size: 64pt (still very large for such a short word)
   - Header spacing: 20px (too much empty space above)
   - Translation spacing: 140px (may still feel cramped)
   - Result: Word dominates, supporting text feels lost

2. **Weekly Phrase "Aye" (3 characters)**:
   - Font size: 68pt (extremely large for single word)
   - Header spacing: 25px
   - Translation spacing: 140px
   - Result: Massive word with excessive whitespace

3. **Weekly Insult "Eejit" (5 characters)**:
   - Font size: 66pt (very large)
   - Header spacing: 15px
   - Translation spacing: 160px
   - Result: Similar issues to word/phrase

### Root Cause Analysis

The algorithms scale font size inversely with length, but:
- **Minimum font sizes are still too large** for very short content (50-68pt range)
- **Spacing calculations don't account for visual weight** - a 64pt "wee" takes up more visual space than a 52pt longer word
- **Vertical positioning** centers content, which for short content creates excessive top/bottom whitespace
- **No consideration of aspect ratio** - short words are tall but narrow, creating imbalance

---

## Requirements

### Aesthetic Goals
1. **Balanced visual hierarchy** - main content prominent but not overwhelming
2. **Appropriate whitespace** - no excessive gaps, no cramped elements
3. **Readability** - all text elements clearly readable
4. **Consistency** - similar content lengths should look similar
5. **Adaptability** - must work for content lengths from 3 to 50+ characters

### Technical Constraints
- Must use ImageMagick for rendering
- Canvas is fixed at 1080×1080px
- Text must be wrapped if it exceeds 800px width
- All measurements use actual rendered dimensions (not estimates)
- Must account for descenders (g, j, p, q, y)

---

## Current Implementation Files

- **Main Renderer**: `utils/weekly_content_image_renderer_v2.py`
- **Optimization Functions**: 
  - `calculate_optimized_font_sizes()` - Lines 30-120
  - `calculate_optimized_spacing()` - Lines 122-200
- **Main Render Function**: `render_weekly_content_image()` - Lines 268-830

---

## Test Data Examples

### Minimalist (Problem Cases):
- **Word**: "wee" (3 chars) → "small" (5 chars translation)
- **Phrase**: "Aye" (3 chars) → "Yes" (3 chars translation)
- **Insult**: "Eejit" (5 chars) → "Idiot" (5 chars translation)

### Maximalist (Acceptable Cases):
- **Word**: "scunner" (7 chars) → "disgust; annoyance; strong dislike" (35 chars)
- **Phrase**: "Keep yersel tae yersel" (24 chars) → "Keep yourself to yourself" (26 chars)
- **Insult**: "Ye're as useful as a chocolate fireguard" (42 chars) → "You are completely useless" (24 chars)

---

## Questions for Expert Guidance

1. **Font Scaling**: Should we use a different scaling function (e.g., logarithmic, square root) instead of linear thresholds?

2. **Minimum Font Sizes**: What are appropriate minimum font sizes for very short content (3-5 characters) that maintain visual balance?

3. **Spacing Strategy**: Should spacing be proportional to font size, or use a different relationship?

4. **Vertical Positioning**: For short content, should we:
   - Position higher on canvas (less centering)?
   - Use different vertical distribution?
   - Add decorative elements to fill space?

5. **Visual Weight**: How should we account for the visual "weight" of text (not just pixel dimensions but perceived size)?

6. **Aspect Ratio**: Should we adjust layout based on the aspect ratio of the text (tall/narrow vs. wide/short)?

7. **Golden Ratio / Design Principles**: Should we apply design principles like golden ratio spacing, rule of thirds, etc.?

8. **Content-Type Specific**: Should each content type (word/phrase/insult) have fundamentally different layout strategies, or should they share a unified approach?

---

## Current Algorithm Summary

**Font Size**: Inverse linear relationship with content length (longer = smaller, but with fixed minimums)

**Spacing**: Linear adjustments based on length and number of lines, with fixed base values

**Positioning**: Centered vertically within available space, with minimum header spacing

**Result**: Works for medium-to-long content, fails for very short content (3-5 characters)

---

## Next Steps Needed

1. **Expert review** of current algorithms and parameters
2. **Alternative scaling functions** for font sizes and spacing
3. **Layout strategies** specifically for short content
4. **Visual weight calculations** to better balance elements
5. **Testing framework** to validate improvements across all content lengths

---

## File Locations

- **Documentation**: `docs/WEEKLY_CONTENT_AESTHETIC_ANALYSIS_AND_OPTIMIZATION.md`
- **This Document**: `docs/WEEKLY_CONTENT_IMAGE_OPTIMIZATION_PARAMETERS.md`
- **Code**: `utils/weekly_content_image_renderer_v2.py`
- **Test Scripts**: 
  - `scripts/test_weekly_content_images_v2.py` (current week examples)
  - `scripts/test_weekly_content_aesthetic_analysis.py` (minimalist/maximalist examples)

---

**Status**: Current implementation produces acceptable results for longer content but "disastrous" results for short content (3-5 characters). Seeking expert guidance on improved algorithms and parameters.
