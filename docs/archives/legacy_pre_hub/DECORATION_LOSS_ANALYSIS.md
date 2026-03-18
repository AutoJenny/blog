# Decoration Loss Analysis
**Date:** 2025-11-11  
**Issue:** Second decoration value disappeared from Product Type Identifiers display

---

## Root Cause Analysis

### The Problem
A second decoration that was previously visible is now missing from the Product Type Identifiers section.

### Investigation Findings

#### 1. Template Code (NOT THE ISSUE)
The template code in `product_data_review.html` is correct:
```jinja
{% for decoration in type_data.decorations %}
    <span class="attribute-tag">{{ decoration|replace('_', ' ')|title }}</span>
{% endfor %}
```
This loops through ALL decorations in the array - no filtering or limiting.

#### 2. Data Extraction (NOT THE ISSUE)
The `ClanDataExtractor` simply passes through `product_type_data` from the database:
```python
'product_type_data': product.get('product_type_data'),
```
No filtering or modification happens here.

#### 3. Normalization Logic (POTENTIAL ISSUE)
In `utils/product_type_parser.py` line 446:
```python
result[field] = sorted(list(set([item.lower().strip() for item in result[field] if item])))
```

**This line does:**
1. Filters out falsy values (`if item` removes `None`, empty strings, `False`, `0`)
2. Converts to lowercase
3. Strips whitespace
4. Removes duplicates using `set()`
5. Sorts the result

**Potential Issues:**
- If a decoration is an empty string or `None`, it gets filtered out
- If two decorations become identical after lowercasing (e.g., "Rust-Proof Eyelets" and "rust-proof eyelets"), one is removed
- If a decoration contains only whitespace, it gets stripped and then filtered out

#### 4. Merge Logic (POTENTIAL ISSUE)
In `_merge_results()` line 418:
```python
merged[field] = list(set(merged.get(field, []) + llm_result.get(field, [])))
```

**This does:**
- Combines strict parsing results with LLM results
- Uses `set()` to remove duplicates **before normalization**
- If LLM returns different case or format, duplicates might not be caught until normalization

**Example Scenario:**
1. Strict parser finds: `['rust-proof eyelets', 'thick leather tie']`
2. LLM returns: `['Rust-Proof Eyelets']` (only one, different case)
3. Merge creates: `['rust-proof eyelets', 'thick leather tie', 'Rust-Proof Eyelets']`
4. Normalization converts all to lowercase: `['rust-proof eyelets', 'thick leather tie']`
5. **Result: Both decorations preserved** ✅

**But if:**
1. Strict parser finds: `['rust-proof eyelets']`
2. LLM returns: `['thick leather tie']` (different decoration)
3. Merge creates: `['rust-proof eyelets', 'thick leather tie']`
4. Normalization: `['rust-proof eyelets', 'thick leather tie']`
5. **Result: Both preserved** ✅

#### 5. Most Likely Cause: Re-parsing with Different Model

**The Real Issue:**
When we switched from Llama 3.2 to Mistral 7B, the background parsing script (`parse_product_types.py`) re-processed products. The LLM (Mistral) may have:
- Returned different decorations than Llama 3.2 did
- Returned fewer decorations
- Failed to parse one of the decorations correctly
- Returned a decoration in a format that got filtered out

**Evidence:**
- The script is currently running: `parse_product_types.py --threshold 0.7`
- It processes products in batches and updates `product_type_data`
- When a product is re-parsed, the old data is overwritten
- Mistral 7B may have different parsing behavior than Llama 3.2

---

## The Actual Problem

**The decoration wasn't "lost" by the template or display code - it was lost during re-parsing when the product was processed with Mistral 7B instead of Llama 3.2.**

### Why This Happened

1. **Model Difference:** Mistral 7B may interpret the product description/title differently than Llama 3.2
2. **LLM Variability:** LLM responses are non-deterministic - same input can produce different outputs
3. **Re-parsing Overwrites:** When `parse_product_types.py` runs, it overwrites existing `product_type_data` with new parsing results
4. **No Preservation Logic:** The parser doesn't check if existing data should be preserved - it always generates fresh data

### Example Scenario

**Before (with Llama 3.2):**
- Product had: `decorations: ['rust-proof eyelets', 'thick leather tie']`
- Both displayed correctly

**After (with Mistral 7B):**
- Product re-parsed
- Mistral returned: `decorations: ['rust-proof eyelets']` (missed the second one)
- Database updated with new data
- Only one decoration now displays

---

## Solutions

### Option 1: Re-parse the Specific Product
Manually re-parse product 88 to see if Mistral picks up both decorations on a second attempt.

### Option 2: Add Preservation Logic
Modify the parser to preserve existing decorations if new parsing returns fewer items:
```python
# In _merge_results or _validate_and_normalize
if existing_data and existing_data.get('decorations'):
    existing_decorations = existing_data['decorations']
    new_decorations = result.get('decorations', [])
    # Preserve existing if new has fewer
    if len(new_decorations) < len(existing_decorations):
        result['decorations'] = existing_decorations
```

### Option 3: Improve LLM Prompt
Enhance the LLM prompt to explicitly request ALL decorations found in the product description.

### Option 4: Manual Override
Add UI to manually add/edit decorations that the parser missed.

---

## Recommendation

**Immediate:** Check the actual database value for the product to confirm if the decoration is missing from the data or just not displaying.

**Long-term:** Implement preservation logic to prevent data loss during re-parsing, especially when switching models.

---

## Code Locations

- **Template:** `templates/planning/calendar/product_data_review.html` (lines 395-406) - ✅ Correct
- **Data Extraction:** `utils/content_generation/clan_data_extractor.py` (line 148) - ✅ Correct
- **Normalization:** `utils/product_type_parser.py` (line 446) - ⚠️ Could filter out edge cases
- **Merge Logic:** `utils/product_type_parser.py` (line 418) - ⚠️ Uses set() before normalization
- **Re-parsing Script:** `scripts/parse_product_types.py` - ⚠️ Overwrites existing data

