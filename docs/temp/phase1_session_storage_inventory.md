# Phase 1.2: Session Storage Violations Inventory

**CRITICAL FINDING**: System using `ui_session_state` table for temporary session-based storage instead of proper database persistence

---

## **DATABASE TABLE: `ui_session_state`**

### **Table Schema:**
- **id**: integer (primary key, not null)
- **session_id**: varchar (not null) - Session identifier
- **user_id**: integer (nullable) - User identifier
- **state_key**: varchar (not null) - State key identifier
- **state_value**: text (nullable) - State value data
- **state_type**: varchar (not null) - Data type (string, json, integer)
- **expires_at**: timestamp (nullable) - Expiration time
- **created_at**: timestamp (nullable) - Creation time
- **updated_at**: timestamp (nullable) - Last update time

### **Current Usage Patterns:**
1. **Selected Product Storage**: `selected_product_id` key
2. **UI State Storage**: Accordion states, filter preferences
3. **Session-based Data**: Platform selections, channel settings

---

## **FILE 1: `blueprints/launchpad.py`**

### **Functions Using `ui_session_state`:**
1. **`get_selected_product()`** (Lines 1551-1555)
2. **`set_selected_product()`** (Lines 1588-1594)

### **Usage Pattern:**
- **Purpose**: Product selection persistence
- **Impact**: CRITICAL - Core product workflow
- **Keys Used**: `selected_product_id`
- **Data Structure**: Integer (product ID)
- **Session ID**: `'global'` (hardcoded)
- **State Type**: `'integer'`

### **SQL Operations:**
```sql
-- GET: Retrieve selected product
SELECT state_value FROM ui_session_state 
WHERE state_key = 'selected_product_id' 
ORDER BY updated_at DESC 
LIMIT 1

-- DELETE: Clear old selection
DELETE FROM ui_session_state WHERE state_key = 'selected_product_id'

-- INSERT: Save new selection
INSERT INTO ui_session_state (session_id, state_key, state_value, state_type, updated_at)
VALUES ('global', 'selected_product_id', %s, 'integer', NOW())
```

---

## **FILE 2: `blueprints/launchpad_content.py`**

### **Functions Using `ui_session_state`:**
1. **`get_selected_product()`** (Lines 406-410)
2. **`set_selected_product()`** (Lines 447-453)

### **Usage Pattern:**
- **Purpose**: Product selection persistence (duplicate functionality)
- **Impact**: CRITICAL - Core product workflow
- **Keys Used**: `selected_product_id`
- **Data Structure**: String (product ID as string)
- **Session ID**: Not provided (causes constraint violations)
- **State Type**: Not provided (causes constraint violations)

### **SQL Operations:**
```sql
-- GET: Retrieve selected product
SELECT state_value FROM ui_session_state 
WHERE state_key = 'selected_product_id' 
ORDER BY updated_at DESC 
LIMIT 1

-- DELETE: Clear old selection
DELETE FROM ui_session_state WHERE state_key = 'selected_product_id'

-- INSERT: Save new selection (BROKEN - missing required fields)
INSERT INTO ui_session_state (state_key, state_value, created_at, updated_at)
VALUES ('selected_product_id', %s, NOW(), NOW())
```

---

## **FILE 3: `blueprints/launchpad_monolithic_backup.py`**

### **Functions Using `ui_session_state`:**
1. **`get_selected_product()`** (Lines 1111-1115)
2. **`set_selected_product()`** (Lines 1148-1154)

### **Usage Pattern:**
- **Purpose**: Product selection persistence (backup version)
- **Impact**: CRITICAL - Core product workflow
- **Keys Used**: `selected_product_id`
- **Data Structure**: Integer (product ID)
- **Session ID**: `'global'` (hardcoded)
- **State Type**: `'integer'`

---

## **CURRENT DATA IN TABLE**

### **Sample Records:**
1. **Platform Selection**: `last_visited_platform` = 'facebook'
2. **UI State**: `accordion_state` = JSON with expanded/collapsed states
3. **Channel Selection**: `selected_channel` = 'feed_post'
4. **Filter Preferences**: `filter_preferences` = JSON with UI preferences
5. **Product Selection**: `selected_product_id` = '4373'

### **Data Types Used:**
- **string**: Platform names, channel names
- **json**: Complex UI state objects
- **integer**: Product IDs

---

## **CRITICAL ISSUES IDENTIFIED**

### **1. Constraint Violations**
- **Error**: `null value in column "session_id" of relation "ui_session_state" violates not-null constraint`
- **Cause**: `launchpad_content.py` not providing required `session_id`
- **Impact**: 500 errors when setting selected product

### **2. Inconsistent Data Types**
- **launchpad.py**: Stores product ID as integer
- **launchpad_content.py**: Stores product ID as string
- **Impact**: Data inconsistency and potential errors

### **3. Duplicate Functionality**
- **Three different files** implementing the same functionality
- **Different implementations** with different error handling
- **Impact**: Code maintenance nightmare

### **4. Session-based Architecture**
- **Violates requirement** for database persistence
- **Data lost** when session expires
- **Not suitable** for multi-user or long-term storage

---

## **IMPACT ASSESSMENT**

### **Critical Impact:**
- **Product Selection**: Core workflow functionality
- **Data Loss Risk**: High - session-based storage
- **System Reliability**: Poor - constraint violations

### **Medium Impact:**
- **UI State**: User experience degradation
- **Code Maintenance**: High complexity

### **Low Impact:**
- **Filter Preferences**: Cosmetic only

---

## **REPLACEMENT STRATEGY NEEDED**

### **1. Replace Session-based Storage**
- Move to proper database tables
- Use foreign key relationships
- Implement proper data types

### **2. Consolidate Duplicate Code**
- Single implementation for product selection
- Consistent data handling
- Proper error handling

### **3. Fix Constraint Violations**
- Ensure all required fields are provided
- Implement proper validation
- Add error handling

---

## **NEXT STEPS**

1. **Phase 1.3**: Document in-memory state violations
2. **Phase 1.4**: Analyze database schema for replacement fields
3. **Phase 2**: Design replacement strategies
4. **Phase 3**: Implement database-backed persistence

---

**Status**: ✅ COMPLETED
**Date**: 2025-09-25
**Next**: Phase 1.3 - In-Memory State Analysis
