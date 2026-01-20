# Final Layout & Aesthetic Specification - Implementation Complete

**Date:** 2026-01-20  
**Status:** ✅ Fully implemented according to authoritative specification

---

## Summary of Changes Implemented

All changes from the "Final Layout & Aesthetic Specification (Authoritative)" document have been implemented in `utils/weekly_content_image_renderer_v2.py`.

---

## 1. Fixed Canvas & Margins

```python
CANVAS_SIZE = 1080
TOP_MARGIN = 90
BOTTOM_MARGIN = 90
FOOTER_SAFETY_GAP = 56  # ✅ Increased from 40 (aesthetic fix)
```

**Why:** Provenance was visually too close to footer. Extra gap provides breathing room.

---

## 2. Height Budgets (Updated)

```python
SCOTS_MAX_HEIGHT = int(CANVAS_SIZE * 0.26)  # 26% = ~280px (unchanged)
TRANSLATION_MAX_HEIGHT = int(CANVAS_SIZE * 0.14)  # ✅ 14% = ~150px (was 12%)
USAGE_MAX_HEIGHT = int(CANVAS_SIZE * 0.22)  # ✅ 22% = ~238px (was 20%)
PROVENANCE_MAX_HEIGHT = int(CANVAS_SIZE * 0.12)  # ✅ 12% = ~130px (was 10%)
```

**Aesthetic change:** Examples and provenance were too small → budgets increased.

---

## 3. Font Sizes (Updated Ranges)

### Header (Fixed)
```python
HEADER_FONT_SIZE = 48  # Fixed, never scales
```

### Scots Main Text
- **Starting sizes:** Word: 56pt, Phrase: 54pt, Insult: 52pt
- **Hard bounds:** 40-56pt
- **Sizing rule:** Aim to fill 80-90% of SCOTS_MAX_HEIGHT
- **Short content:** Clamp to 48-52pt (never below 48pt)

### Translation
```python
# ✅ Font size range: 32-38pt (was 30-36pt)
# Max width: 760px
# Max height: TRANSLATION_MAX_HEIGHT (14% = ~150px)
```

**Change:** Translation should be clearly readable, not metadata-small.

### Usage Examples
```python
# ✅ Font size range: 28-34pt (was 26-32pt)
# Line height multiplier: 1.35 (was 1.3)
# Max combined height: USAGE_MAX_HEIGHT (22% = ~238px)
```

**Change:** Usage examples should feel nearly as important as translation, not secondary clutter.

### Provenance / Notes
```python
# ✅ Font size range: 24-28pt (was 22-26pt)
# Max width: 720px
# Max height: PROVENANCE_MAX_HEIGHT (12% = ~130px)
# Max lines: 3
# Line height multiplier: 1.3
```

**Change:** Provenance must never feel crushed or glued to the footer.

### Footer (Fixed)
```python
FOOTER_FONT_SIZE = 24  # Fixed, never scales
```

---

## 4. Spacing Rules (Updated Clamps)

### Header → Scots
```python
header_to_scots = clamp(24, int(scots_height * 0.35), 64)  # ✅ Max increased to 64px
```

### Scots → Translation
```python
scots_to_translation = clamp(
    60 if is_short_content else 48,  # ✅ Min 60px for short content
    int(scots_height * 0.30),
    100  # ✅ Max increased to 100px
)
```

### Translation → Usage
```python
translation_to_usage = clamp(
    42,  # ✅ Min increased to 42px
    int(translation_height * 0.30),  # ✅ Changed from 0.25
    84  # ✅ Max increased to 84px
)
```

### Usage → Provenance
```python
usage_to_provenance = clamp(
    36,  # ✅ Min increased to 36px
    int(usage_height * 0.25),  # ✅ Changed from 0.20
    72  # ✅ Max increased to 72px
)
```

### Provenance → Footer
```python
provenance_to_footer = FOOTER_SAFETY_GAP  # 56px (was 40px)
```

---

## 5. Layout Order (CRITICAL - Implemented Exactly)

### Step 1 – Measure all blocks
✅ All blocks measured before positioning (header, Scots, translation, usage, provenance, footer)

### Step 2 – Compute all spacings
✅ Using final rendered heights

### Step 3 – Compute total content height
✅ **INCLUDING provenance** (not excluding it)
```python
total_content_height = (
    scots_height +
    scots_to_translation +
    translation_height +
    translation_to_usage +
    usage_height +
    usage_to_provenance +
    provenance_height  # ✅ INCLUDED
)
```

### Step 4 – Weighted centering inside content band
```python
if total_content_height < content_band_height:
    remaining = content_band_height - total_content_height
    offset = int(remaining * 0.35)  # ✅ NOT 50%
    scots_y = content_band_top + offset
else:
    scots_y = content_band_top
```

### Step 5 – Single top-down placement pass
```python
scots_y
translation_y = scots_bottom + scots_to_translation
usage_y = translation_bottom + translation_to_usage
provenance_y = usage_bottom + usage_to_provenance  # ✅ Flows from usage, NOT bottom-anchored
```

**Key Change:** Provenance is now part of the top-down flow, NOT bottom-anchored. This ensures single-pass layout with no collision correction.

---

## 6. Absolute Invariant (Updated)

**Old:** `content_bottom <= footer_top`

**New:** `provenance_bottom <= content_band_bottom`

```python
if provenance_bottom > content_band_bottom:
    # Shrink in priority order:
    # 1. Provenance
    # 2. Usage
    # 3. Translation
    # 4. Scots (last resort)
    # Never move blocks after placement
```

---

## 7. Short Content Detection (Unchanged - Already Correct)

```python
is_single_line = len(scots_lines) == 1
is_narrow = scots_width < (PHRASE_MAX_WIDTH * 0.40)
is_low_glyph_count = scots_length <= 5

is_short_content = is_single_line and (is_narrow or is_low_glyph_count)
```

---

## Key Architectural Changes

1. ✅ **FOOTER_SAFETY_GAP increased to 56px** - Better footer breathing room
2. ✅ **Height budgets increased** - Translation 14%, Usage 22%, Provenance 12%
3. ✅ **Font sizes increased** - Translation 32-38pt, Usage 28-34pt, Provenance 24-28pt
4. ✅ **Spacing clamps updated** - All minimums/maximums adjusted per spec
5. ✅ **Layout order corrected** - Provenance included in total_content_height, single top-down pass
6. ✅ **Provenance flows from usage** - NOT bottom-anchored (ensures single-pass layout)
7. ✅ **Invariant check updated** - Checks `provenance_bottom <= content_band_bottom`

---

## Visual Improvements Expected

- ✅ Short content feels confident, not tiny
- ✅ Examples easy to read on mobile (larger font)
- ✅ Provenance feels informative, not decorative (larger font)
- ✅ Footer feels separate, not attached to content (56px gap)
- ✅ White space feels intentional, not accidental (weighted centering)

---

## QA Checklist (Visual Red Flags)

Reject renders if:
- ❌ Provenance touches or nearly touches footer
- ❌ Usage text is smaller than translation
- ❌ Short words look lost at the top
- ❌ Large empty zones appear above or below content
- ❌ Any text touches canvas edges

---

**File:** `utils/weekly_content_image_renderer_v2.py`  
**Last Updated:** 2026-01-20 (Final Layout Specification Implementation)
