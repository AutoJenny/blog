# Phase 2.3: Migration Strategy Design

## **MIGRATION OVERVIEW**

This document outlines the strategy for migrating from unauthorized storage (localStorage, ui_session_state, in-memory state) to the new persistent database tables.

## **MIGRATION PHASES**

### **Phase 1: Infrastructure Setup**
- [ ] Create new database tables
- [ ] Implement API endpoints
- [ ] Create migration scripts
- [ ] Set up testing framework

### **Phase 2: Data Migration**
- [ ] Migrate existing data from `ui_session_state`
- [ ] Create data mapping scripts
- [ ] Validate migrated data
- [ ] Test API endpoints

### **Phase 3: Code Migration**
- [ ] Update JavaScript modules to use new APIs
- [ ] Replace localStorage calls
- [ ] Replace in-memory state objects
- [ ] Update event handlers

### **Phase 4: Cleanup**
- [ ] Remove localStorage usage
- [ ] Remove ui_session_state table
- [ ] Remove in-memory state objects
- [ ] Update documentation

## **DETAILED MIGRATION PLAN**

### **1. Database Table Creation**

#### **Migration Script: `migrations/create_ui_state_tables.sql`**
```sql
-- Create ui_selection_state table
CREATE TABLE ui_selection_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    selection_type VARCHAR(50) NOT NULL,
    selected_id INTEGER,
    selected_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, selection_type)
);

-- Create ui_ui_state table
CREATE TABLE ui_ui_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    state_key VARCHAR(100) NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, state_key)
);

-- Create ui_workflow_state table
CREATE TABLE ui_workflow_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    workflow_id VARCHAR(100) NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, workflow_id)
);

-- Create ui_queue_state table
CREATE TABLE ui_queue_state (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    page_type VARCHAR(50) NOT NULL,
    queue_type VARCHAR(50) NOT NULL,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_type, queue_type)
);

-- Create indexes for performance
CREATE INDEX idx_ui_selection_state_user_page ON ui_selection_state(user_id, page_type);
CREATE INDEX idx_ui_ui_state_user_page ON ui_ui_state(user_id, page_type);
CREATE INDEX idx_ui_workflow_state_user_page ON ui_workflow_state(user_id, page_type);
CREATE INDEX idx_ui_queue_state_user_page ON ui_queue_state(user_id, page_type);
```

### **2. Data Migration from ui_session_state**

#### **Migration Script: `migrations/migrate_ui_session_state.py`**
```python
#!/usr/bin/env python3
"""
Migrate data from ui_session_state to new state tables
"""

from config.database import db_manager
import json
from datetime import datetime

def migrate_ui_session_state():
    """Migrate data from ui_session_state to new tables"""
    
    with db_manager.get_cursor() as cursor:
        # Get all ui_session_state records
        cursor.execute("""
            SELECT user_id, state_key, state_value, state_type, created_at
            FROM ui_session_state
            WHERE state_value IS NOT NULL
        """)
        
        records = cursor.fetchall()
        print(f"Found {len(records)} records to migrate")
        
        for record in records:
            user_id = record['user_id'] or 1
            state_key = record['state_key']
            state_value = record['state_value']
            state_type = record['state_type']
            created_at = record['created_at']
            
            try:
                # Parse state_value as JSON
                state_data = json.loads(state_value) if state_value else {}
                
                # Map to appropriate table based on state_key
                if state_key == 'selected_product_id':
                    migrate_selection_state(cursor, user_id, state_data, created_at)
                elif state_key.startswith('accordion_') or state_key.startswith('tab_'):
                    migrate_ui_state(cursor, user_id, state_key, state_data, created_at)
                elif state_key.startswith('llm_') or state_key.startswith('generation_'):
                    migrate_workflow_state(cursor, user_id, state_key, state_data, created_at)
                elif state_key.startswith('queue_'):
                    migrate_queue_state(cursor, user_id, state_key, state_data, created_at)
                else:
                    print(f"Unknown state_key: {state_key}")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {state_key}: {e}")
                continue
            except Exception as e:
                print(f"Error migrating {state_key}: {e}")
                continue

def migrate_selection_state(cursor, user_id, state_data, created_at):
    """Migrate selection state"""
    cursor.execute("""
        INSERT INTO ui_selection_state 
        (user_id, page_type, selection_type, selected_id, selected_data, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, page_type, selection_type) 
        DO UPDATE SET 
            selected_id = EXCLUDED.selected_id,
            selected_data = EXCLUDED.selected_data,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, 'product_post', 'product', state_data.get('product_id'), 
          json.dumps(state_data), created_at))

def migrate_ui_state(cursor, user_id, state_key, state_data, created_at):
    """Migrate UI state"""
    # Determine page_type from state_key or default
    page_type = 'product_post'  # Default, could be determined from context
    
    cursor.execute("""
        INSERT INTO ui_ui_state 
        (user_id, page_type, state_key, state_data, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, page_type, state_key) 
        DO UPDATE SET 
            state_data = EXCLUDED.state_data,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, page_type, state_key, json.dumps(state_data), created_at))

def migrate_workflow_state(cursor, user_id, state_key, state_data, created_at):
    """Migrate workflow state"""
    page_type = 'product_post'  # Default
    workflow_id = state_key.replace('llm_', '').replace('generation_', '')
    
    cursor.execute("""
        INSERT INTO ui_workflow_state 
        (user_id, page_type, workflow_id, state_data, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, page_type, workflow_id) 
        DO UPDATE SET 
            state_data = EXCLUDED.state_data,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, page_type, workflow_id, json.dumps(state_data), created_at))

def migrate_queue_state(cursor, user_id, state_key, state_data, created_at):
    """Migrate queue state"""
    page_type = 'product_post'  # Default
    queue_type = state_key.replace('queue_', '')
    
    cursor.execute("""
        INSERT INTO ui_queue_state 
        (user_id, page_type, queue_type, state_data, created_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, page_type, queue_type) 
        DO UPDATE SET 
            state_data = EXCLUDED.state_data,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, page_type, queue_type, json.dumps(state_data), created_at))

if __name__ == "__main__":
    migrate_ui_session_state()
    print("Migration completed")
```

### **3. JavaScript Module Updates**

#### **New State Manager: `static/js/state-manager.js`**
```javascript
/**
 * Centralized state management using database persistence
 * Replaces localStorage, sessionStorage, and in-memory state
 */

class StateManager {
    constructor(userId = 1) {
        this.userId = userId;
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30 seconds
    }

    // Selection State Management
    async getSelection(pageType, selectionType) {
        const cacheKey = `selection_${pageType}_${selectionType}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/selection-state?page_type=${pageType}&selection_type=${selectionType}`);
            const data = await response.json();
            
            if (data.selections && data.selections.length > 0) {
                const selection = data.selections[0];
                this.cache.set(cacheKey, selection);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return selection;
            }
            return null;
        } catch (error) {
            console.error('Error getting selection:', error);
            return null;
        }
    }

    async setSelection(pageType, selectionType, selectedId, selectedData) {
        try {
            const response = await fetch('/api/ui/selection-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    selection_type: selectionType,
                    selected_id: selectedId,
                    selected_data: selectedData
                })
            });

            if (response.ok) {
                const cacheKey = `selection_${pageType}_${selectionType}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting selection:', error);
            return false;
        }
    }

    // UI State Management
    async getUIState(pageType, stateKey) {
        const cacheKey = `ui_${pageType}_${stateKey}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/ui-state?page_type=${pageType}&state_key=${stateKey}`);
            const data = await response.json();
            
            if (data.ui_states && data.ui_states.length > 0) {
                const state = data.ui_states[0];
                this.cache.set(cacheKey, state);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return state;
            }
            return null;
        } catch (error) {
            console.error('Error getting UI state:', error);
            return null;
        }
    }

    async setUIState(pageType, stateKey, stateData) {
        try {
            const response = await fetch('/api/ui/ui-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    state_key: stateKey,
                    state_data: stateData
                })
            });

            if (response.ok) {
                const cacheKey = `ui_${pageType}_${stateKey}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting UI state:', error);
            return false;
        }
    }

    // Workflow State Management
    async getWorkflowState(pageType, workflowId) {
        const cacheKey = `workflow_${pageType}_${workflowId}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/workflow-state?page_type=${pageType}&workflow_id=${workflowId}`);
            const data = await response.json();
            
            if (data.workflow_states && data.workflow_states.length > 0) {
                const state = data.workflow_states[0];
                this.cache.set(cacheKey, state);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return state;
            }
            return null;
        } catch (error) {
            console.error('Error getting workflow state:', error);
            return null;
        }
    }

    async setWorkflowState(pageType, workflowId, stateData) {
        try {
            const response = await fetch('/api/ui/workflow-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    workflow_id: workflowId,
                    state_data: stateData
                })
            });

            if (response.ok) {
                const cacheKey = `workflow_${pageType}_${workflowId}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting workflow state:', error);
            return false;
        }
    }

    // Queue State Management
    async getQueueState(pageType, queueType) {
        const cacheKey = `queue_${pageType}_${queueType}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            const response = await fetch(`/api/ui/queue-state?page_type=${pageType}&queue_type=${queueType}`);
            const data = await response.json();
            
            if (data.queue_states && data.queue_states.length > 0) {
                const state = data.queue_states[0];
                this.cache.set(cacheKey, state);
                setTimeout(() => this.cache.delete(cacheKey), this.cacheTimeout);
                return state;
            }
            return null;
        } catch (error) {
            console.error('Error getting queue state:', error);
            return null;
        }
    }

    async setQueueState(pageType, queueType, stateData) {
        try {
            const response = await fetch('/api/ui/queue-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    page_type: pageType,
                    queue_type: queueType,
                    state_data: stateData
                })
            });

            if (response.ok) {
                const cacheKey = `queue_${pageType}_${queueType}`;
                this.cache.delete(cacheKey);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error setting queue state:', error);
            return false;
        }
    }

    // Clear all state for a page
    async clearPageState(pageType) {
        try {
            const response = await fetch(`/api/ui/state?page_type=${pageType}`, {
                method: 'DELETE'
            });
            return response.ok;
        } catch (error) {
            console.error('Error clearing page state:', error);
            return false;
        }
    }
}

// Global instance
window.stateManager = new StateManager();
```

### **4. Migration Testing**

#### **Test Script: `scripts/test_migration.py`**
```python
#!/usr/bin/env python3
"""
Test the migration from unauthorized storage to new state tables
"""

import requests
import json
from config.database import db_manager

def test_migration():
    """Test that migration worked correctly"""
    
    # Test API endpoints
    base_url = "http://localhost:5000"
    
    # Test selection state
    response = requests.get(f"{base_url}/api/ui/selection-state?page_type=product_post&selection_type=product")
    print(f"Selection state API: {response.status_code}")
    
    # Test UI state
    response = requests.get(f"{base_url}/api/ui/ui-state?page_type=product_post&state_key=accordion_states")
    print(f"UI state API: {response.status_code}")
    
    # Test workflow state
    response = requests.get(f"{base_url}/api/ui/workflow-state?page_type=product_post&workflow_id=content_generation")
    print(f"Workflow state API: {response.status_code}")
    
    # Test queue state
    response = requests.get(f"{base_url}/api/ui/queue-state?page_type=product_post&queue_type=posting_queue")
    print(f"Queue state API: {response.status_code}")
    
    # Check database records
    with db_manager.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM ui_selection_state")
        selection_count = cursor.fetchone()[0]
        print(f"Selection state records: {selection_count}")
        
        cursor.execute("SELECT COUNT(*) FROM ui_ui_state")
        ui_count = cursor.fetchone()[0]
        print(f"UI state records: {ui_count}")
        
        cursor.execute("SELECT COUNT(*) FROM ui_workflow_state")
        workflow_count = cursor.fetchone()[0]
        print(f"Workflow state records: {workflow_count}")
        
        cursor.execute("SELECT COUNT(*) FROM ui_queue_state")
        queue_count = cursor.fetchone()[0]
        print(f"Queue state records: {queue_count}")

if __name__ == "__main__":
    test_migration()
```

## **ROLLBACK STRATEGY**

If migration fails:
1. Keep `ui_session_state` table intact
2. Revert JavaScript changes
3. Restore localStorage functionality
4. Fix migration issues
5. Retry migration

## **VALIDATION CHECKLIST**

- [ ] All API endpoints return correct data
- [ ] JavaScript modules use new state manager
- [ ] No localStorage calls remain
- [ ] No in-memory state objects
- [ ] Page refreshes maintain state
- [ ] Cross-page state persistence works
- [ ] Performance is acceptable
- [ ] Error handling works correctly

## **NEXT STEPS**

1. Create database migration scripts
2. Implement API endpoints
3. Create state manager JavaScript
4. Update existing modules
5. Test migration
6. Deploy and monitor

---

**Status**: Ready for implementation
**Dependencies**: API endpoint design (Phase 2.2 completed)
**Next Phase**: Implementation plan (Phase 2.4)
