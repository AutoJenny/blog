# Mistral Low Confidence Products - Quick Summary

**Date:** 2025-11-12  
**Total:** 33 products with confidence < 0.7  
**Main Issue:** `core_type` = `None` for all 33 products

---

## Key Patterns Identified

### 1. Missing from CORE_TYPES (Need to Add)

**Homeware:**
- `mouse_mat` (3 products)
- `drink_coaster` (2 products)  
- `pet_bowl` (1 product)
- `door_mat` (1 product)
- `bath_mat` (1 product)
- `laptop_sleeve` (2 products)
- `backpack` (2 products)
- `notebook` (1 product)
- `mug` (1 product)
- `magnet` (1 product)
- `flag` (1 product)
- `ornament` (1 product)

**Clothing:**
- `hoodie` (1 product)
- `crop_top` (1 product)
- `shorts` (1 product)
- `sports_bra` (1 product)
- `poncho` (1 product)

**Accessories:**
- `pin` (5 products: lapel pin, tie pin, dog pins)
- `garter` (1 product - note: `garters` plural exists)
- `duffle_bag` (1 product)

**Other:**
- `swatch` (1 product - exists but not matching)

### 2. In CORE_TYPES but Not Matching

- **`cummerbund`** - Exists but "Essential Tartan Cummerbund" → `None`
- **`swatch`** - Exists but "Fabric Swatch" → `None`  
- **`chopping_board`** - Exists but "Glass Chopping Board" → `None`
- **`garters`** - Exists (plural) but "Wedding Garter" (singular) → `None`

---

## Root Causes

### Cause 1: Limited Garment Keyword Matching
The `_strict_parse` method only checks a small `garment_keywords` dict (lines 218-224) that doesn't include:
- `cummerbund` (even though it's in CORE_TYPES)
- `hoodie`, `shorts`, `sports_bra`, `poncho`, `crop_top`

### Cause 2: Compound Names Not Handled
- "Mouse Mat" → should be `mouse_mat` but parser doesn't check compound names
- "Laptop Sleeve" → should be `laptop_sleeve`
- "Drink Coaster" → should be `drink_coaster`
- "Crop Top" → should be `crop_top`
- "Sports Bra" → should be `sports_bra`

### Cause 3: Descriptive Prefixes Block Matching
- "Glass Chopping Board" → prefix "Glass" prevents matching `chopping_board`
- "Fabric Swatch" → prefix "Fabric" prevents matching `swatch`
- "Tartan Mug" → prefix "Tartan" prevents matching `mug`

### Cause 4: Pin Logic Too Specific
The pin matching logic (lines 170-177) only handles:
- "kilt pin" → `kilt_pin`
- "tie slide" → `tie_slide`
- "keyring" → `keyring`

But doesn't handle:
- "Lapel Pin" → should be `pin`
- "Tie Pin" → should be `pin`
- "Dog Pin" → should be `pin`

### Cause 5: Plural/Singular Mismatch
- `garters` exists in CORE_TYPES but "Wedding Garter" (singular) doesn't match

---

## Recommended Fixes

### Fix 1: Add Missing Core Types
Add to `CORE_TYPES` set in `utils/product_type_parser.py`:

```python
# Add these to CORE_TYPES:
'mouse_mat', 'drink_coaster', 'pet_bowl', 'door_mat', 'bath_mat',
'laptop_sleeve', 'backpack', 'notebook', 'mug', 'magnet', 'flag',
'ornament', 'hoodie', 'crop_top', 'shorts', 'sports_bra', 'poncho',
'pin', 'garter', 'duffle_bag', 'place_mat', 'bar_runner', 'pencil_case',
'tank_top', 'flip_flops', 'rash_guard', 'swimsuit', 'swim_trunks',
'tote_bag', 'shopping_bag'
```

### Fix 2: Expand Garment Keywords
Add to `garment_keywords` dict in `_strict_parse`:

```python
garment_keywords = {
    'kilt': 'kilt', 'shirt': 'shirt', 'jacket': 'jacket',
    'waistcoat': 'waistcoat', 'sporran': 'sporran', 'tie': 'tie',
    'scarf': 'scarf', 'tam': 'tam', 'hat': 'hat', 'skirt': 'skirt',
    'dress': 'dress', 'trousers': 'trousers', 'sweater': 'sweater',
    'cardigan': 'cardigan',
    # ADD THESE:
    'cummerbund': 'cummerbund', 'hoodie': 'hoodie', 'shorts': 'shorts',
    'sports bra': 'sports_bra', 'poncho': 'poncho', 'crop top': 'crop_top',
    'tank top': 'tank_top', 'flip flops': 'flip_flops', 'rash guard': 'rash_guard',
    'swimsuit': 'swimsuit', 'swim trunks': 'swim_trunks'
}
```

### Fix 3: Handle Compound Names
Add compound name matching before garment keywords:

```python
# Check compound names
compound_names = {
    'mouse mat': 'mouse_mat',
    'laptop sleeve': 'laptop_sleeve',
    'drink coaster': 'drink_coaster',
    'pet bowl': 'pet_bowl',
    'door mat': 'door_mat',
    'bath mat': 'bath_mat',
    'crop top': 'crop_top',
    'sports bra': 'sports_bra',
    'tank top': 'tank_top',
    'flip flops': 'flip_flops',
    'rash guard': 'rash_guard',
    'swim trunks': 'swim_trunks',
    'place mat': 'place_mat',
    'bar runner': 'bar_runner',
    'pencil case': 'pencil_case',
    'tote bag': 'tote_bag',
    'shopping bag': 'shopping_bag',
    'chopping board': 'chopping_board'
}
for compound, core_type in compound_names.items():
    if compound in name_lower:
        result['core_type'] = core_type
        result['confidence'] = 0.75
        break
```

### Fix 4: Strip Descriptive Prefixes
Add prefix stripping before checking CORE_TYPES:

```python
# Strip common descriptive prefixes
prefixes_to_strip = ['glass', 'fabric', 'tartan', 'clan crest', 'premium', 
                     'essential', 'classic', 'luxury', 'irish', 'celtic']
name_cleaned = name_lower
for prefix in prefixes_to_strip:
    if name_cleaned.startswith(prefix + ' '):
        name_cleaned = name_cleaned[len(prefix) + 1:].strip()
    elif ' ' + prefix + ' ' in name_cleaned:
        name_cleaned = name_cleaned.replace(' ' + prefix + ' ', ' ').strip()

# Then check name_cleaned against CORE_TYPES
```

### Fix 5: Improve Pin Matching
Update pin logic to handle all pin types:

```python
if 'pin' in name_lower:
    if 'kilt' in name_lower:
        result['core_type'] = 'kilt_pin'
    elif 'tie' in name_lower or 'lapel' in name_lower:
        result['core_type'] = 'pin'  # Generic pin
    else:
        result['core_type'] = 'pin'  # Generic pin
    result['disambiguation']['is_accessory'] = True
    result['disambiguation']['product_form'] = 'accessory'
    result['confidence'] = 0.85
```

### Fix 6: Handle Plural/Singular
Add normalization:

```python
# Normalize plurals
name_normalized = name_lower
if name_normalized.endswith('s') and len(name_normalized) > 3:
    # Try singular form
    singular = name_normalized[:-1]
    if singular in self.CORE_TYPES:
        result['core_type'] = singular
        result['confidence'] = 0.75
```

---

## Implementation Priority

1. **High Priority** - Add missing core types (Fix 1)
2. **High Priority** - Handle compound names (Fix 3)
3. **Medium Priority** - Strip descriptive prefixes (Fix 4)
4. **Medium Priority** - Expand garment keywords (Fix 2)
5. **Low Priority** - Improve pin matching (Fix 5)
6. **Low Priority** - Handle plural/singular (Fix 6)

---

## Expected Impact

After implementing these fixes:
- **33 products** should get proper `core_type` values
- **Confidence scores** should improve from 0.60-0.65 to 0.75-0.85
- **Mistral processing** should be more accurate with better examples

---

## Testing

After fixes, re-run:
```bash
python scripts/parse_product_types.py --mistral-only --threshold 0.7
python scripts/review_product_types.py --mistral-only --threshold 0.7
```

Expected result: Most or all 33 products should have proper `core_type` values and higher confidence scores.


