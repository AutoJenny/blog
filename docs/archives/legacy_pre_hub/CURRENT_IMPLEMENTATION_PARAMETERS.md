# Current Implementation Parameters - What Was Actually Coded

**Date:** 2026-01-20  
**Status:** Images are "MUCH worse than before" - documenting actual parameters for review

---

## Canvas Constants

```python
CANVAS_SIZE = 1080
TOP_MARGIN = 90
BOTTOM_MARGIN = 90
FOOTER_SAFETY_GAP = 40
PHRASE_MAX_WIDTH = 800
```

---

## Height Budgets (as % of canvas)

```python
SCOTS_MAX_HEIGHT = int(CANVAS_SIZE * 0.26)  # 26% = 280px
TRANSLATION_MAX_HEIGHT = int(CANVAS_SIZE * 0.12)  # 12% = 130px
USAGE_MAX_HEIGHT = int(CANVAS_SIZE * 0.20)  # 20% = 216px
PROVENANCE_MAX_HEIGHT = int(CANVAS_SIZE * 0.10)  # 10% = 108px
```

---

## Font Size Calculation Functions

### 1. Scots Text (`calculate_scots_font_size_by_height`)

**Starting Font Sizes:**
- `weekly_word`: 56pt
- `weekly_phrase`: 54pt
- `weekly_insult`: 52pt

**Hard Caps:**
- Maximum: 56pt
- Minimum: 40pt

**Algorithm:**
```python
for font_size in range(start_size, min_font - 1, -2):  # Decrease by 2pt each step
    width, height, lines = _measure_text_dimensions(scots_text, BODY_FONT, font_size, 800)
    if height <= max_height:  # max_height = 280px (26% of canvas)
        return font_size, height, lines
# If none fit, use minimum 40pt
```

**Short Content Handling:**
```python
is_short_content = len(scots_lines) == 1 and scots_height < 120
if is_short_content and scots_font_size > 48:
    scots_font_size = 48  # Cap at 48pt for short content
```

---

### 2. Translation (`calculate_translation_font_size`)

**Font Size Range:** 30-36pt

**Max Height:** 130px (12% of canvas)

**Max Width:** 760px

**Algorithm:**
```python
for font_size in range(36, 29, -2):  # Try 36, 34, 32, 30
    width, height, _ = _measure_text_dimensions(translation_text, ACCENT_FONT, font_size, 760)
    if height <= 130:
        return font_size, height
# If none fit, use minimum 30pt
```

---

### 3. Usage Examples (`calculate_usage_font_size`)

**Font Size Range:** 26-32pt

**Max Combined Height:** 216px (20% of canvas)

**Line Spacing:** 55px between examples

**Algorithm:**
```python
for font_size in range(32, 25, -2):  # Try 32, 30, 28, 26
    total_height = sum(usage_heights) + (len(heights) - 1) * 55
    if total_height <= 216:
        return font_size, total_height
# If none fit, use minimum 26pt
```

---

### 4. Provenance/Notes (`calculate_provenance_font_size`)

**Font Size Range:** 22-26pt

**Max Height:** 108px (10% of canvas)

**Max Width:** 720px

**Max Lines:** 3 (truncates with ellipsis if more)

**Algorithm:**
```python
for font_size in range(26, 21, -2):  # Try 26, 24, 22
    width, height, lines = _measure_text_dimensions(notes, ACCENT_FONT, font_size, 720)
    if len(lines) > 3:
        lines = lines[:3]
        lines[2] = lines[2][:-3] + "..."  # Truncate with ellipsis
    if height <= 108:
        return font_size, height, lines
# If none fit, use minimum 22pt
```

---

## Proportional Spacing (`calculate_proportional_spacing`)

**Rules:**
```python
header_to_scots = int(scots_height * 0.35)  # Clamped to 24-60px
scots_to_translation = int(scots_height * 0.30)
translation_to_usage = int(translation_height * 0.25)  # Only if usage exists
usage_to_provenance = int(usage_height * 0.20)  # Only if usage exists
provenance_to_footer = 40  # Fixed
```

**Short Content Adjustment:**
```python
if is_short_content:
    header_to_scots = int(header_to_scots * 0.8)  # Reduce by 20%
```

---

## Layout Flow (Top-Down, No Centering)

**Position Calculation:**
```python
header_bottom = TOP_MARGIN + header_height + header_to_scots
scots_y = header_bottom  # NO CENTERING - starts immediately after header
scots_bottom = scots_y + scots_height
translation_y = scots_bottom + scots_to_translation
translation_bottom = translation_y + trans_height

if usage_font_size > 0:
    usage_start_y = translation_bottom + translation_to_usage
    usage_bottom = usage_start_y + total_usage_height
else:
    usage_bottom = translation_bottom

if provenance_font_size > 0:
    provenance_y = usage_bottom + (usage_to_provenance if usage_font_size > 0 else 0)
else:
    provenance_y = 0

footer_top = CANVAS_SIZE - BOTTOM_MARGIN - footer_height - provenance_to_footer
```

---

## Absolute Invariant Enforcement

**Check:**
```python
total_used_height = (
    scots_height +
    scots_to_translation +
    trans_height +
    (translation_to_usage if usage_font_size > 0 else 0) +
    total_usage_height +
    (usage_to_provenance if usage_font_size > 0 and provenance_font_size > 0 else 0) +
    provenance_height +
    provenance_to_footer
)

content_bottom = header_bottom + total_used_height

if content_bottom > footer_top:
    # Shrink in priority: provenance → usage → translation → Scots (last resort)
```

---

## Fixed Font Sizes (Never Change)

```python
HEADER_FONT_SIZE = 48pt
FOOTER_FONT_SIZE = 24pt
```

---

## Text Wrapping Max Widths

```python
Scots text: 800px
Translation: 760px
Provenance: 720px
```

---

## Issues That May Be Causing "Much Worse" Results

1. **Scots font size too small for short content**: Starting at 56pt and reducing to fit 280px may make "wee" (3 chars) too small
2. **Proportional spacing too tight**: 0.30 × Scots height for short words (e.g., 40px height) = only 12px spacing
3. **Top-down flow too rigid**: No centering means short content sits very high, leaving huge bottom gap
4. **Height budgets too restrictive**: 26% max for Scots may be forcing font sizes too small
5. **Short content detection**: Only triggers if 1 line AND < 120px, may not catch all short cases

---

## Actual Values Being Used (Example: "wee" - 3 characters)

**Scots:**
- Start: 56pt
- Max height: 280px
- Result: Likely 40-48pt (fits in 280px)
- Height: ~80-100px

**Spacing:**
- header_to_scots: 0.35 × 100px = 35px (clamped 24-60px) → 35px
- scots_to_translation: 0.30 × 100px = 30px (very tight!)

**Translation:**
- Font: 30-36pt (tries to fit in 130px)
- Height: ~40-50px

**Total spacing from header to translation:**
- header_to_scots: 35px
- scots_height: ~100px
- scots_to_translation: 30px
- **Total: ~165px from top margin**

This leaves ~800px of empty space below for a 3-character word!

---

## Code Location

All functions in: `utils/weekly_content_image_renderer_v2.py`

- Lines 48-80: `calculate_scots_font_size_by_height`
- Lines 83-100: `calculate_translation_font_size`
- Lines 103-136: `calculate_usage_font_size`
- Lines 139-182: `calculate_provenance_font_size`
- Lines 185-217: `calculate_proportional_spacing`
- Lines 478-850: `render_weekly_content_image` (main function)
