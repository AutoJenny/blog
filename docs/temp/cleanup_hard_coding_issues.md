# Hard-Coding Issues Cleanup

**Date:** 2025-01-27  
**Issue:** Field persistence not working due to hard-coded values in step configuration

## Issues Found and Fixed

### 1. Step Configuration Hard-Coding (FIXED)
**Location:** `workflow_step_entity` table, step ID 41 (Initial Concept)  
**Problem:** Output field had `"db_field": "basic_idea"` hard-coded in the step configuration  
**Impact:** Field selector could not dynamically set the output field, causing persistence issues  
**Fix:** Updated step configuration to set `db_field` to empty string (`""`)  
**SQL:** 
```sql
UPDATE workflow_step_entity 
SET config = jsonb_set(config, '{outputs,output1,db_field}', '""'::jsonb) 
WHERE id = 41;
```

### 2. LLM Models API Column Mismatch (FIXED)
**Location:** `app/api/workflow/routes.py` - `get_llm_models()` function  
**Problem:** API was querying non-existent columns `model_name` and `provider_name` from `llm_action` table  
**Impact:** 500 Internal Server Error when loading LLM models in workflow UI  
**Fix:** Updated query to use correct column names `llm_model` and joined with `llm_provider` table  
**SQL Fix:**
```sql
-- Before (incorrect):
SELECT DISTINCT model_name, provider_name FROM llm_action

-- After (correct):
SELECT DISTINCT la.llm_model, lp.name as provider_name
FROM llm_action la
JOIN llm_provider lp ON la.provider_id = lp.id
```

## Issues Identified for Future Cleanup

### 3. API Endpoint Documentation Inconsistency
**Location:** `/docs/database/schema.md`  
**Problem:** Documentation references deprecated `/api/v1/post/{post_id}/development` endpoint  
**Impact:** Confusion about correct API endpoints  
**Status:** ✅ FIXED - Updated to correct `/api/workflow/posts/{post_id}/development`

### 4. Step Configuration Consistency Risk
**Location:** `workflow_step_entity` table  
**Problem:** Other steps may have similar hard-coded field mappings that conflict with dynamic field selector  
**Impact:** Could cause similar persistence issues in other workflow steps  
**Action Required:** Audit all step configurations for hard-coded `db_field` values

### 5. Field Selector Fallback Logic Risk
**Location:** `app/static/modules/llm_panel/js/field_selector.js`  
**Problem:** Fallback mechanism uses target element's `data-db-field` attribute, which could cause issues if templates have hard-coded values  
**Impact:** Could override user selections with template defaults  
**Action Required:** Review fallback logic and ensure it doesn't override user selections

### 6. Step ID Hard-Coding
**Location:** `app/static/modules/llm_panel/js/field_selector.js` - `getCurrentStepId()` method  
**Problem:** Hard-coded step ID (`41`) for Initial Concept step  
**Impact:** Could break if database structure changes or step IDs are reassigned  
**Action Required:** Implement dynamic step ID detection

## Recommended Actions

1. **Audit Step Configurations:** Check all `workflow_step_entity` records for hard-coded `db_field` values
2. **Review Template Hard-Coding:** Ensure no templates have hard-coded `data-db-field` attributes
3. **Implement Dynamic Step ID Detection:** Replace hard-coded step IDs with dynamic detection
4. **Add Validation:** Prevent hard-coded field mappings from being saved in step configurations

## Files Modified

- `docs/database/schema.md` - Updated API endpoint documentation
- `workflow_step_entity` table - Removed hard-coded `basic_idea` from step 41 configuration
- `app/api/workflow/routes.py` - Fixed LLM models API endpoint to use correct column names

## Testing

- ✅ Output field persistence now works correctly
- ✅ Field selector can dynamically set output field
- ✅ User selections persist across page reloads
- ✅ API endpoints working correctly
- ✅ LLM models API now returns correct data without errors
- ✅ Console errors resolved 