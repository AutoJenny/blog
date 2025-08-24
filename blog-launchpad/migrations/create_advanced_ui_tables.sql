-- =====================================================
-- ADVANCED UI & OPERATIONAL TABLES - PHASE 4
-- Social Media Database Framework Completion
-- =====================================================

-- =====================================================
-- 1. UI SECTIONS TABLE
-- =====================================================
CREATE TABLE ui_sections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    section_type VARCHAR(50) NOT NULL, -- 'platform', 'channel', 'process', 'global'
    parent_section_id INTEGER REFERENCES ui_sections(id),
    display_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT true,
    is_collapsible BOOLEAN DEFAULT true,
    default_collapsed BOOLEAN DEFAULT false,
    color_theme VARCHAR(50), -- 'primary', 'secondary', 'success', 'warning', 'danger', 'info'
    icon_class VARCHAR(100), -- FontAwesome or custom icon classes
    css_classes TEXT, -- Additional CSS classes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. UI MENU ITEMS TABLE
-- =====================================================
CREATE TABLE ui_menu_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    menu_type VARCHAR(50) NOT NULL, -- 'main', 'sidebar', 'dropdown', 'context'
    parent_menu_id INTEGER REFERENCES ui_menu_items(id),
    section_id INTEGER REFERENCES ui_sections(id),
    url_pattern VARCHAR(255),
    icon_class VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    requires_permission VARCHAR(100), -- Permission required to see this menu item
    badge_text VARCHAR(50), -- For showing counts or status
    badge_color VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. UI DISPLAY RULES TABLE
-- =====================================================
CREATE TABLE ui_display_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL, -- 'conditional', 'permission', 'status', 'custom'
    target_type VARCHAR(50) NOT NULL, -- 'section', 'menu_item', 'field', 'button'
    target_id INTEGER, -- ID of the target element
    condition_expression TEXT, -- JSON or custom expression for the rule
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0, -- Higher priority rules are evaluated first
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. CONTENT PRIORITIES TABLE
-- =====================================================
CREATE TABLE content_priorities (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL, -- 'platform', 'channel', 'process', 'post'
    content_id INTEGER NOT NULL, -- ID of the content item
    priority_score DECIMAL(8,4) NOT NULL DEFAULT 0,
    priority_factors JSONB, -- Store the factors that contributed to this score
    last_calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_calculation_at TIMESTAMP,
    calculation_version VARCHAR(20), -- Version of the priority algorithm used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_type, content_id)
);

-- =====================================================
-- 5. PRIORITY FACTORS TABLE
-- =====================================================
CREATE TABLE priority_factors (
    id SERIAL PRIMARY KEY,
    factor_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    factor_type VARCHAR(50) NOT NULL, -- 'recency', 'activity', 'engagement', 'custom'
    weight DECIMAL(5,4) NOT NULL DEFAULT 1.0, -- Weight in priority calculation (0.0 to 1.0)
    calculation_formula TEXT, -- Formula or logic for calculating this factor
    is_active BOOLEAN DEFAULT true,
    is_configurable BOOLEAN DEFAULT true, -- Can users adjust this factor?
    min_value DECIMAL(10,4),
    max_value DECIMAL(10,4),
    default_value DECIMAL(10,4),
    unit VARCHAR(50), -- Unit of measurement
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 6. UI USER PREFERENCES TABLE
-- =====================================================
CREATE TABLE ui_user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL, -- Reference to your user system
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    preference_type VARCHAR(50) NOT NULL, -- 'boolean', 'string', 'number', 'json'
    category VARCHAR(100), -- Group related preferences
    is_global BOOLEAN DEFAULT false, -- Apply to all users if true
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- =====================================================
-- 7. UI SESSION STATE TABLE
-- =====================================================
CREATE TABLE ui_session_state (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id INTEGER, -- Optional, for authenticated users
    state_key VARCHAR(100) NOT NULL,
    state_value TEXT,
    state_type VARCHAR(50) NOT NULL, -- 'json', 'string', 'number', 'boolean'
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, state_key)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- UI Sections indexes
CREATE INDEX idx_ui_sections_section_type ON ui_sections(section_type);
CREATE INDEX idx_ui_sections_parent_section_id ON ui_sections(parent_section_id);
CREATE INDEX idx_ui_sections_display_order ON ui_sections(display_order);
CREATE INDEX idx_ui_sections_is_visible ON ui_sections(is_visible);

-- UI Menu Items indexes
CREATE INDEX idx_ui_menu_items_menu_type ON ui_menu_items(menu_type);
CREATE INDEX idx_ui_menu_items_parent_menu_id ON ui_menu_items(parent_menu_id);
CREATE INDEX idx_ui_menu_items_section_id ON ui_menu_items(section_id);
CREATE INDEX idx_ui_menu_items_display_order ON ui_menu_items(display_order);
CREATE INDEX idx_ui_menu_items_is_visible ON ui_menu_items(is_visible);

-- UI Display Rules indexes
CREATE INDEX idx_ui_display_rules_rule_type ON ui_display_rules(rule_type);
CREATE INDEX idx_ui_display_rules_target_type ON ui_display_rules(target_type);
CREATE INDEX idx_ui_display_rules_target_id ON ui_display_rules(target_id);
CREATE INDEX idx_ui_display_rules_priority ON ui_display_rules(priority);
CREATE INDEX idx_ui_display_rules_is_active ON ui_display_rules(is_active);

-- Content Priorities indexes
CREATE INDEX idx_content_priorities_content_type ON content_priorities(content_type);
CREATE INDEX idx_content_priorities_content_id ON content_priorities(content_id);
CREATE INDEX idx_content_priorities_priority_score ON content_priorities(priority_score);
CREATE INDEX idx_content_priorities_last_calculated_at ON content_priorities(last_calculated_at);

-- Priority Factors indexes
CREATE INDEX idx_priority_factors_factor_type ON priority_factors(factor_type);
CREATE INDEX idx_priority_factors_weight ON priority_factors(weight);
CREATE INDEX idx_priority_factors_is_active ON priority_factors(is_active);

-- UI User Preferences indexes
CREATE INDEX idx_ui_user_preferences_user_id ON ui_user_preferences(user_id);
CREATE INDEX idx_ui_user_preferences_preference_key ON ui_user_preferences(preference_key);
CREATE INDEX idx_ui_user_preferences_category ON ui_user_preferences(category);
CREATE INDEX idx_ui_user_preferences_is_global ON ui_user_preferences(is_global);

-- UI Session State indexes
CREATE INDEX idx_ui_session_state_session_id ON ui_session_state(session_id);
CREATE INDEX idx_ui_session_state_user_id ON ui_session_state(user_id);
CREATE INDEX idx_ui_session_state_expires_at ON ui_session_state(expires_at);

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================
COMMENT ON TABLE ui_sections IS 'Defines UI sections and their display properties';
COMMENT ON TABLE ui_menu_items IS 'Defines menu items and navigation structure';
COMMENT ON TABLE ui_display_rules IS 'Defines conditional display rules for UI elements';
COMMENT ON TABLE content_priorities IS 'Stores calculated priority scores for content items';
COMMENT ON TABLE priority_factors IS 'Defines factors used in priority calculations';
COMMENT ON TABLE ui_user_preferences IS 'Stores user-specific UI preferences';
COMMENT ON TABLE ui_session_state IS 'Stores temporary UI state for user sessions';

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

