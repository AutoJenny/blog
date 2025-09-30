# Hardcoded Values Recovery Plan
## Critical Issue Resolution Protocol

**Date:** 2025-01-29  
**Status:** CRITICAL - All development halted until resolved  
**Protocol:** Each fix requires explicit permission and verification before proceeding

---

## 🚨 **ISSUE SUMMARY**

Unauthorized hardcoded values were introduced in the authoring system without permission, creating a catastrophic risk of data corruption and system failure. All hardcoded values must be systematically identified, analyzed, and replaced with proper database queries.

---

## 📋 **COMPLETE AUDIT OF HARDCODED VALUES**

### **Issue #1: Backend API Hardcoded Topics**
**File:** `blueprints/authoring.py`  
**Lines:** 536, 569  
**Code:**
```python
'topics': ['Celtic Roots of Samhain Traditions', 'The History of Ceres Festival in Modern Scotland', 'Samhain Traditions in Scottish Christianity']
'SECTION_TOPICS': 'Celtic Roots of Samhain Traditions, The History of Ceres Festival in Modern Scotland, Samhain Traditions in Scottish Christianity'
```

**Context:** Fallback data in `api_generate_section_draft()` function  
**Impact:** All section generation uses fake data instead of real planning data

### **Issue #2: Frontend Hardcoded Group Title**
**File:** `templates/authoring/sections/drafting.html`  
**Line:** 951  
**Code:**
```javascript
document.getElementById('section-group-display').textContent = 'Historical Foundations of Autumnal Traditions';
```

**Context:** `loadSectionContext()` function  
**Impact:** All sections show the same fake group title

### **Issue #3: Frontend Hardcoded Group Summary**
**File:** `templates/authoring/sections/drafting.html`  
**Line:** 954  
**Code:**
```javascript
document.getElementById('section-group-summary-display').textContent = 'This group explores the Celtic roots and historical developments that shaped Scotland\'s autumnal customs, highlighting their significance in understanding the country\'s identity.';
```

**Context:** `loadSectionContext()` function  
**Impact:** All sections show the same fake group explanation

### **Issue #4: Frontend Hardcoded Topics Display**
**File:** `templates/authoring/sections/drafting.html`  
**Lines:** 959-961  
**Code:**
```javascript
<span class="topic-tag">Celtic Roots of Samhain Traditions</span>
<span class="topic-tag">The History of Ceres Festival in Modern Scotland</span>
<span class="topic-tag">Samhain Traditions in Scottish Christianity</span>
```

**Context:** `loadSectionContext()` function  
**Impact:** All sections show the same fake topics

### **Issue #5: Frontend Hardcoded Avoid Topics**
**File:** `templates/authoring/sections/drafting.html`  
**Lines:** 967-972  
**Code:**
```javascript
<div><strong>Agriculture and the Land's Bounty</strong> (Crop rotation practices in ancient Scotland, Agricultural cycle and Celtic mythology, Crops in Scottish folk remedies)</div>
<div><strong>Seasonal Celebrations: Timeless Traditions</strong> (Modern harvest festivals, Community celebrations, Seasonal observances)</div>
// ... more hardcoded sections
```

**Context:** `loadSectionContext()` function  
**Impact:** All sections show the same fake avoid topics list

---

## 🔍 **SYSTEMATIC ANALYSIS OF DATA SOURCES**

### **Current Database State Investigation**

#### **1. `post_development.sections` Field**
**Current State:** `"[object Object],[object Object],[object Object],[object Object],[object Object],[object Object],[object Object]"`  
**Expected State:** Proper JSON with section data including topics, group info, explanations  
**Root Cause:** JSON serialization failure during planning workflow  
**Investigation Needed:** Check if raw data exists in other tables

#### **2. `post_section` Table**
**Current State:** Basic section data (heading, description, order)  
**Missing:** Topics, group explanations, avoid topics  
**Investigation Needed:** Check if this table has the data we need

#### **3. Planning Workflow Tables**
**Investigation Needed:** Check if grouping and titling results are stored elsewhere
- `workflow_step_results` table
- `llm_prompt_results` table
- Any other planning data storage

### **API Endpoints Analysis**

#### **Current Endpoints:**
1. `/planning/api/posts/<id>` - Returns corrupted sections data
2. `/authoring/api/posts/<id>/sections/<section_id>` - Returns basic section data
3. `/planning/api/posts/<id>/sections` - Needs investigation

#### **Missing Endpoints:**
1. Proper section data with topics and group info
2. Avoid topics calculation endpoint
3. Group explanation retrieval endpoint

---

## 🛠️ **PROPOSED FIXES**

### **Fix #1: Backend API Hardcoded Topics**
**Priority:** CRITICAL  
**Approach:** Replace hardcoded topics with proper database query

**Required Research:**
1. Investigate `post_development.sections` corruption
2. Check if planning data exists in other tables
3. Determine if data can be recovered or must be regenerated

**Proposed Solution:**
1. Create proper API endpoint to get section topics from planning data
2. Replace hardcoded topics with database query
3. Add error handling for missing data (NO hardcoded fallbacks)

**Implementation Steps:**
1. Research current data state
2. Create proper data retrieval function
3. Replace hardcoded values
4. Add proper error handling

**Test:** Generate section draft and verify topics come from database, not hardcoded values

### **Fix #2: Frontend Hardcoded Group Title**
**Priority:** CRITICAL  
**Approach:** Replace hardcoded group title with API call

**Required Research:**
1. Determine where group titles are stored in planning data
2. Check if group titles exist in `post_section` table
3. Verify API endpoint exists to retrieve group data

**Proposed Solution:**
1. Create API call to get group title for specific section
2. Replace hardcoded value with dynamic data
3. Add error handling for missing data

**Implementation Steps:**
1. Research group title data source
2. Create API endpoint if needed
3. Replace hardcoded value
4. Add error handling

**Test:** Load section page and verify group title comes from database

### **Fix #3: Frontend Hardcoded Group Summary**
**Priority:** CRITICAL  
**Approach:** Replace hardcoded group summary with API call

**Required Research:**
1. Determine where group explanations are stored
2. Check if explanations exist in planning workflow results
3. Verify if explanations were generated during grouping step

**Proposed Solution:**
1. Create API call to get group explanation
2. Replace hardcoded value with dynamic data
3. Add error handling for missing data

**Implementation Steps:**
1. Research group explanation data source
2. Create API endpoint if needed
3. Replace hardcoded value
4. Add error handling

**Test:** Load section page and verify group summary comes from database

### **Fix #4: Frontend Hardcoded Topics Display**
**Priority:** CRITICAL  
**Approach:** Replace hardcoded topics with API call

**Required Research:**
1. Determine where section topics are stored
2. Check if topics exist in planning workflow results
3. Verify if topics were generated during brainstorming step

**Proposed Solution:**
1. Create API call to get section topics
2. Replace hardcoded HTML with dynamic generation
3. Add error handling for missing data

**Implementation Steps:**
1. Research topics data source
2. Create API endpoint if needed
3. Replace hardcoded HTML
4. Add error handling

**Test:** Load section page and verify topics come from database

### **Fix #5: Frontend Hardcoded Avoid Topics**
**Priority:** CRITICAL  
**Approach:** Replace hardcoded avoid topics with API call

**Required Research:**
1. Determine how to calculate avoid topics from other sections
2. Check if all sections data is available
3. Verify if topics exist for all sections

**Proposed Solution:**
1. Create API call to get all other sections' topics
2. Replace hardcoded HTML with dynamic generation
3. Add error handling for missing data

**Implementation Steps:**
1. Research avoid topics calculation
2. Create API endpoint if needed
3. Replace hardcoded HTML
4. Add error handling

**Test:** Load section page and verify avoid topics are calculated from other sections

---

## 🔬 **INVESTIGATION PROTOCOL**

### **Phase 1: Data State Investigation**
1. **Check `post_development.sections` corruption**
   - Query raw data
   - Determine if data can be recovered
   - Check if data exists elsewhere

2. **Check planning workflow data**
   - Query brainstorming results
   - Query grouping results
   - Query titling results

3. **Check `post_section` table**
   - Verify current data structure
   - Check if missing data can be added

### **Phase 2: API Endpoint Investigation**
1. **Test existing endpoints**
   - Verify what data they return
   - Check for missing endpoints

2. **Identify required endpoints**
   - List all data needed
   - Determine which endpoints are missing

### **Phase 3: Data Recovery Options**
1. **Option A: Recover corrupted data**
   - If possible, fix JSON serialization
   - Restore proper data structure

2. **Option B: Regenerate from planning workflow**
   - Re-run planning steps if data exists
   - Generate proper sections data

3. **Option C: Manual data entry**
   - If no other option, create proper data structure
   - Enter real data manually

---

## ✅ **VERIFICATION PROTOCOL**

### **For Each Fix:**
1. **Pre-implementation:**
   - Full git commit of current state
   - Document current behavior
   - Get explicit permission to proceed

2. **Implementation:**
   - Make only the specific change
   - No additional modifications
   - Document what was changed

3. **Verification:**
   - Test the specific fix
   - Verify no hardcoded values remain
   - Confirm data comes from database

4. **User Verification:**
   - User tests the fix
   - User confirms it works
   - User approves proceeding to next fix

### **Success Criteria:**
- All hardcoded values removed
- All data comes from database
- Proper error handling for missing data
- No fallback to hardcoded values

---

## 🚨 **CRITICAL WARNINGS**

1. **NO HARDCODED VALUES:** Under no circumstances should hardcoded values be used as fallbacks
2. **NO ASSUMPTIONS:** Every data source must be verified before use
3. **NO RUSHING:** Each fix must be thoroughly tested before proceeding
4. **NO SILENT FAILURES:** All errors must be properly handled and reported

---

## 📝 **NEXT STEPS**

1. **Create full git commit** of current state
2. **Begin Phase 1 investigation** of data state
3. **Report findings** and get permission for each fix
4. **Implement fixes one by one** with verification at each step

**This document will be updated as we progress through each fix.**
