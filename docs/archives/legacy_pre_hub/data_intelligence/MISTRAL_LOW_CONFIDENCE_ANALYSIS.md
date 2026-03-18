# Mistral Low Confidence Products Analysis

**Date:** 2025-11-12  
**Total Products:** 33 Mistral-processed products with confidence < 0.7  
**Main Issue:** Most products have `core_type` = `None` despite being classifiable

---

## Key Findings

### 1. Missing Core Types in Master List

Many product types are not in the `CORE_TYPES` master list, causing Mistral to return `None`:

#### Homeware/Kitchen Items (Missing):
- `mouse_mat` - Mouse Mat, Large Mouse Mat
- `drink_coaster` - Drink Coaster, Premium Drink Coaster
- `pet_bowl` - Pet Bowl
- `door_mat` - Indoor Door Mat
- `bath_mat` - Bath Mat
- `laptop_sleeve` - Laptop Sleeve
- `backpack` - Backpack, Classic Backpack, Simple Backpack
- `notebook` - Spiral Notebook
- `flag` - Flag
- `mug` - Mug (11oz, 15oz, etc.)
- `magnet` - Fridge Magnet (rectangular, round)

#### Clothing Items (Missing):
- `hoodie` - Hoodie
- `crop_top` - Crop Top, Long Sleeve Crop Top
- `shorts` - Athletic Long Shorts, Shorts
- `sports_bra` - Padded Sports Bra, Sports Bra
- `poncho` - Poncho, Small Poncho

#### Accessories (Missing):
- `pin` - Lapel Pin, Tie Pin (various types)
- `garter` - Wedding Garter (note: `garters` plural exists but not singular)
- `duffle_bag` - Duffle Bag

#### Other (Missing):
- `ornament` - Ceramic Ornament

### 2. Existing Core Types Not Being Matched

Some products should match existing `CORE_TYPES` but don't:

- **`cummerbund`** - Exists in list but "Essential Tartan Cummerbund" → `None`
- **`swatch`** - Exists in list but "Fabric Swatch" → `None`
- **`chopping_board`** - Exists in list but "Glass Chopping Board" → `None`
- **`garters`** - Exists (plural) but "Wedding Garter" (singular) → `None`

### 3. Pattern Analysis

#### Pattern 1: Compound Names
Products with compound names aren't being recognized:
- "Laptop Sleeve" → should be `laptop_sleeve`
- "Drink Coaster" → should be `drink_coaster`
- "Mouse Mat" → should be `mouse_mat`
- "Pet Bowl" → should be `pet_bowl`
- "Crop Top" → should be `crop_top`
- "Sports Bra" → should be `sports_bra`

#### Pattern 2: Descriptive Prefixes
Products with descriptive prefixes aren't matching:
- "Glass Chopping Board" → should match `chopping_board`
- "Fabric Swatch" → should match `swatch`
- "Tartan Mug" → should match `mug` (if added)
- "Clan Crest Flag" → should match `flag` (if added)

#### Pattern 3: Plural vs Singular
- "Garter" (singular) doesn't match "garters" (plural in list)
- Need to handle both forms

#### Pattern 4: Sports/Athletic Clothing
Many sports/athletic items aren't classified:
- Athletic Long Shorts
- Padded Sports Bra
- Sports Top
- Rash Guard
- Tank Top
- Flip Flops

---

## Recommendations

### 1. Add Missing Core Types

Add to `CORE_TYPES` in `utils/product_type_parser.py`:

```python
# Homeware/Kitchen
'mouse_mat', 'drink_coaster', 'pet_bowl', 'door_mat', 'bath_mat',
'laptop_sleeve', 'backpack', 'notebook', 'flag', 'mug', 'magnet',
'place_mat', 'bar_runner', 'pencil_case',

# Clothing
'hoodie', 'crop_top', 'shorts', 'sports_bra', 'poncho', 'tank_top',
'flip_flops', 'rash_guard', 'swimsuit', 'swim_trunks',

# Accessories
'pin', 'garter', 'duffle_bag', 'tote_bag', 'shopping_bag',

# Other
'ornament', 'garter'  # Note: garter already exists as garters
```

### 2. Improve Pattern Matching

#### A. Handle Compound Names
Update `_strict_parse` to handle compound names:
- Split on spaces and check for multi-word matches
- "laptop sleeve" → `laptop_sleeve`
- "drink coaster" → `drink_coaster`
- "mouse mat" → `mouse_mat`

#### B. Handle Descriptive Prefixes
Strip common prefixes before matching:
- "Glass Chopping Board" → "Chopping Board" → `chopping_board`
- "Fabric Swatch" → "Swatch" → `swatch`
- "Tartan Mug" → "Mug" → `mug`
- "Clan Crest Flag" → "Flag" → `flag`

#### C. Handle Plural/Singular
Normalize plurals:
- "garter" → "garters" (check plural form)
- "pin" → "pins" (check plural form)
- Or add both forms to CORE_TYPES

### 3. Improve LLM Prompt

Update the Mistral prompt to:
1. Be more explicit about compound names
2. Provide examples of how to handle descriptive prefixes
3. Include examples of the missing types

### 4. Add Validation Rules

Add post-processing rules:
- If `core_type` is `None` but product name contains known keywords, set a default
- Example: "Mouse Mat" → if `core_type` is `None`, check for "mouse mat" → set `mouse_mat`

---

## Products by Category

### Homeware/Kitchen (13 products)
- Mouse Mat (3 variants)
- Drink Coaster (2 variants)
- Pet Bowl (1)
- Chopping Board (1)
- Door Mat (1)
- Bath Mat (1)
- Laptop Sleeve (2 variants)
- Backpack (2 variants)
- Notebook (1)
- Mug (1)
- Magnet (1)

### Clothing (7 products)
- Hoodie (1)
- Crop Top (1)
- Shorts (1)
- Sports Bra (1)
- Garter (1)
- Cummerbund (2 variants)
- Poncho (1)

### Accessories (6 products)
- Pin (5 variants: Lapel, Tie, Dog pins)
- Duffle Bag (1)

### Other (7 products)
- Flag (1)
- Ornament (1)
- Swatch (1)
- Flag (1)

---

## Next Steps

1. **Add missing core types** to `CORE_TYPES` set
2. **Improve pattern matching** to handle compound names and prefixes
3. **Update Mistral prompt** with better examples
4. **Add validation rules** for post-processing
5. **Re-run parsing** on these 33 products
6. **Monitor results** and iterate

---

## Code Changes Needed

### File: `utils/product_type_parser.py`

1. **Add to CORE_TYPES** (line 66-83)
2. **Update `_strict_parse`** to handle:
   - Compound names (split and check)
   - Descriptive prefixes (strip common prefixes)
   - Plural/singular normalization
3. **Update `_llm_parse` prompt** with examples of missing types
4. **Add `_post_process_none_core_type`** method to catch missed classifications





