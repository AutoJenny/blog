# Corrected Implementation Parameters - After Layout Strategy Fixes

**Date:** 2026-01-20  
**Status:** Post-correction implementation with content band, weighted centering, and proper spacing clamps

---

## Canvas & Margins (Unchanged)

```python
CANVAS_SIZE = 1080  # 1080×1080px square
TOP_MARGIN = 90
BOTTOM_MARGIN = 90
FOOTER_SAFETY_GAP = 40
PHRASE_MAX_WIDTH = 800  # Max width for Scots text
```

---

## Height Budgets (as % of canvas)

```python
SCOTS_MAX_HEIGHT = int(CANVAS_SIZE * 0.26)  # 26% = 280px
TRANSLATION_MAX_HEIGHT = int(CANVAS_SIZE * 0.12)  # 12% = 130px
USAGE_MAX_HEIGHT = int(CANVAS_SIZE * 0.20)  # 20% = 216px
PROVENANCE_MAX_HEIGHT = int(CANVAS_SIZE * 0.10)  # 10% = 108px
```

**Note:** These are **ceilings**, not targets. Content should fill 80-90% of budget when possible.

---

## Content Band (NEW - Key Fix)

```python
content_band_top = header_bottom  # After header + header_to_scots spacing
content_band_bottom = CANVAS_SIZE - BOTTOM_MARGIN - footer_height - provenance_to_footer
content_band_height = content_band_bottom - content_band_top  # ~60-65% of canvas (~750px)
```

**Purpose:** Defines the vertical region where all main content lives. Prevents top-hugging and bottom voids.

**Weighted Centering Logic:**
```python
if total_content_height < content_band_height:
    remaining_space = content_band_height - total_content_height
    offset = int(remaining_space * 0.35)  # 35% offset (NOT 50%)
    scots_y = content_band_top + offset
else:
    scots_y = content_band_top  # Start at top if content fills/exceeds band
```

---

## Font Size Calculation

### 1. Header (Fixed)
```python
HEADER_FONT_SIZE = 48  # Fixed, never scales
```

### 2. Scots Text (`calculate_scots_font_size_by_height`)

**Starting Font Sizes:**
- `weekly_word`: 56pt
- `weekly_phrase`: 54pt
- `weekly_insult`: 52pt

**Hard Caps:**
- Maximum: 56pt
- Minimum: 40pt
- **Short content:** 48-52pt (doesn't shrink unnecessarily)

**Algorithm (CORRECTED - "Fill Band" not "Shrink to Fit"):**
```python
target_height_min = int(max_height * 0.80)  # 80% of budget
target_height_max = int(max_height * 0.90)  # 90% of budget

# Try decreasing font sizes, looking for one that fills target range
for font_size in range(start_size, min_font - 1, -2):
    width, height, lines = measure_text(...)
    
    if target_height_min <= height <= target_height_max:
        return font_size, height, lines  # Found ideal size
    
    # Remember best fit as fallback
    if height <= max_height:
        best_font = font_size
        best_height = height
```

**Key Change:** Now tries to **fill 80-90% of budget**, not just "fit within budget".

### 3. Translation (`calculate_translation_font_size`)

**Font Size Range:** 30-36pt  
**Max Height:** 12% of canvas (130px)  
**Max Width:** 760px  
**Algorithm:** Iteratively decreases from 36pt until height ≤ max_height

### 4. Usage Examples (`calculate_usage_font_size`)

**Font Size Range:** 26-32pt  
**Line Height Multiplier:** 1.3  
**Max Combined Height:** 20% of canvas (216px)  
**Algorithm:** Iteratively decreases from 32pt, reduces line spacing if needed, truncates with ellipsis if still too tall

### 5. Provenance (`calculate_provenance_font_size`)

**Font Size Range:** 22-26pt  
**Max Width:** 720px (narrower than translation)  
**Max Height:** 10% of canvas (108px)  
**Max Lines:** 3 (truncates with ellipsis)  
**Algorithm:** Iteratively decreases from 26pt, reduces line spacing, truncates if necessary

### 6. Footer (Fixed)
```python
FOOTER_FONT_SIZE = 24  # Fixed, never scales
```

---

## Spacing Rules (CORRECTED - Proper Visual Minimums)

### Function: `calculate_proportional_spacing(scots_height, translation_height, usage_height, is_short_content)`

**Header → Scots:**
```python
header_to_scots = int(scots_height * 0.35)
header_to_scots = max(24, min(60, header_to_scots))  # Clamp 24-60px
```

**Scots → Translation (KEY FIX):**
```python
scots_to_translation = int(scots_height * 0.30)
if is_short_content:
    scots_to_translation = max(60, scots_to_translation)  # Minimum 60px for short content
else:
    scots_to_translation = max(48, min(96, scots_to_translation))  # Clamp 48-96px
```

**Translation → Usage:**
```python
translation_to_usage = int(translation_height * 0.25)
translation_to_usage = max(36, min(72, translation_to_usage))  # Clamp 36-72px
```

**Usage → Provenance:**
```python
usage_to_provenance = int(usage_height * 0.20)
usage_to_provenance = max(24, min(60, usage_to_provenance))  # Clamp 24-60px
```

**Provenance → Footer:**
```python
provenance_to_footer = 40  # Fixed
```

**Key Changes:**
- **Scots → Translation minimum is 48px (60px for short content)** - prevents typographic collision
- **Short content gets MORE spacing, not less** - opposite of old behavior
- All spacing has proper visual minimums, not just mathematical clamps

---

## Short Content Detection (CORRECTED)

**Old (Broken):**
```python
is_short_content = len(scots_lines) == 1 and scots_height < 120  # Height-dependent = circular
```

**New (Fixed):**
```python
is_single_line = len(scots_lines) == 1
is_narrow = scots_width < (PHRASE_MAX_WIDTH * 0.40)  # Less than 40% of max width
is_low_glyph_count = scots_length <= 5

is_short_content = is_single_line and (is_narrow or is_low_glyph_count)
```

**Short Content Handling:**
```python
if is_short_content:
    if scots_font_size < 48:
        scots_font_size = 48  # Raise to minimum
    elif scots_font_size > 52:
        scots_font_size = 52  # Cap at 52pt
```

**Key Change:** Detects based on **aspect ratio and visual mass**, not just height.

---

## Layout Flow (CORRECTED - Content Band + Weighted Centering)

### Old (Broken):
```python
scots_y = header_bottom  # Always hugs top
# ... top-down flow ...
# Result: Dead space at bottom, top-heavy
```

### New (Fixed):
```python
# 1. Define content band
content_band_top = header_bottom
content_band_bottom = CANVAS_SIZE - BOTTOM_MARGIN - footer_height - provenance_to_footer
content_band_height = content_band_bottom - content_band_top

# 2. Calculate total content height (without provenance)
total_content_height_no_provenance = (
    scots_height +
    scots_to_translation +
    trans_height +
    translation_to_usage +
    total_usage_height +
    usage_to_provenance
)

# 3. Weighted centering (35% offset, not 50%)
if total_content_height_no_provenance < content_band_height:
    remaining_space = content_band_height - total_content_height_no_provenance
    offset = int(remaining_space * 0.35)  # 35% offset
    scots_y = content_band_top + offset
else:
    scots_y = content_band_top  # Start at top if content fills/exceeds band

# 4. Calculate positions (top-down flow within band)
scots_bottom = scots_y + scots_height
translation_y = scots_bottom + scots_to_translation
translation_bottom = translation_y + trans_height
# ... etc ...
```

**Key Change:** Content is **distributed within band**, not always at top.

---

## Provenance Positioning (CORRECTED - Bottom-Anchored)

### Old (Broken):
```python
provenance_y = usage_bottom + usage_to_provenance  # Flows from usage
# Result: Feels "stuck on", unstable
```

### New (Fixed):
```python
# Provenance is BOTTOM-ANCHORED within content band
if provenance_font_size > 0:
    provenance_y = content_band_bottom - provenance_height
    provenance_bottom = provenance_y + provenance_height
    
    # If provenance overlaps usage, shift usage up
    if usage_font_size > 0 and usage_bottom > provenance_y:
        overlap = usage_bottom - provenance_y + 10  # 10px buffer
        usage_start_y -= overlap
        # Recalculate positions upward if needed
```

**Key Change:** Provenance is **stable and integrated**, not flowing from usage.

---

## Absolute Invariant (Unchanged - Still Enforced)

```python
content_bottom = header_bottom + (
    scots_height +
    scots_to_translation +
    trans_height +
    translation_to_usage +
    total_usage_height +
    usage_to_provenance +
    provenance_height +
    provenance_to_footer
)

if content_bottom > footer_top:
    # Shrink in priority order:
    # 1. Provenance
    # 2. Usage
    # 3. Translation
    # 4. Scots (last resort)
```

**Note:** This prevents overflow, but **does not solve composition** - that's handled by content band + weighted centering.

---

## Summary of Key Corrections

1. ✅ **Content Band:** Defines vertical region (~60-65% of canvas) where content lives
2. ✅ **Weighted Centering:** 35% offset (not 50%) when content < band height
3. ✅ **Spacing Clamps:** Proper visual minimums (48px Scots→Translation, 60px for short content)
4. ✅ **Font Sizing:** "Fill 80-90% of budget" not "shrink to fit"
5. ✅ **Short Content Detection:** Based on aspect ratio + glyph count, not just height
6. ✅ **Bottom-Anchored Provenance:** Stable positioning, not flowing from usage

---

## What This Fixes

**Old Problems:**
- Short content collapsed at top
- Everything felt tiny, crushed, empty
- Massive dead space at bottom
- Proportional spacing too tight for short content
- Font sizing accepted "fits early" instead of filling budget

**New Behavior:**
- Content distributed within band (not top-hugging)
- Short content gets proper spacing (60px minimum)
- Font sizes fill 80-90% of budget (not unnecessarily small)
- Provenance stable and integrated
- Visual balance improved through weighted centering

---

**File:** `utils/weekly_content_image_renderer_v2.py`  
**Last Updated:** 2026-01-20 (after layout strategy corrections)
