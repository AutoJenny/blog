-- =====================================================
-- SEED ADVANCED UI & OPERATIONAL TABLES
-- Sample data for Phase 4 completion
-- =====================================================

-- =====================================================
-- 1. SEED UI SECTIONS
-- =====================================================
INSERT INTO ui_sections (name, display_name, description, section_type, parent_section_id, display_order, is_visible, is_collapsible, default_collapsed, color_theme, icon_class, css_classes) VALUES
-- Global sections
('social_media_dashboard', 'Social Media Dashboard', 'Main dashboard for social media management', 'global', NULL, 1, true, true, false, 'primary', 'fas fa-chart-line', 'dashboard-section'),
('platform_management', 'Platform Management', 'Manage social media platforms and their settings', 'global', NULL, 2, true, true, false, 'info', 'fas fa-cogs', 'platform-section'),
('content_workflow', 'Content Workflow', 'Manage content creation and publishing workflow', 'global', NULL, 3, true, true, false, 'success', 'fas fa-tasks', 'workflow-section'),

-- Platform-specific sections
('facebook_overview', 'Facebook Overview', 'Facebook platform overview and status', 'platform', 2, 1, true, true, false, 'primary', 'fab fa-facebook', 'facebook-section'),
('facebook_channels', 'Facebook Channels', 'Facebook channel-specific configurations', 'platform', 2, 2, true, true, false, 'info', 'fas fa-list', 'channels-section'),
('facebook_analytics', 'Facebook Analytics', 'Facebook performance and analytics', 'platform', 2, 3, true, true, true, 'success', 'fas fa-chart-bar', 'analytics-section'),

-- Channel-specific sections
('feed_post_config', 'Feed Post Configuration', 'Feed post specific settings and requirements', 'channel', 5, 1, true, true, false, 'primary', 'fas fa-edit', 'feed-config'),
('story_post_config', 'Story Post Configuration', 'Story post specific settings and requirements', 'channel', 5, 2, true, true, false, 'info', 'fas fa-mobile-alt', 'story-config'),
('reels_post_config', 'Reels Configuration', 'Reels specific settings and requirements', 'channel', 5, 3, true, true, false, 'success', 'fas fa-video', 'reels-config'),
('group_post_config', 'Group Post Configuration', 'Group post specific settings and requirements', 'channel', 5, 4, true, true, false, 'warning', 'fas fa-users', 'group-config');

-- =====================================================
-- 2. SEED UI MENU ITEMS
-- =====================================================
INSERT INTO ui_menu_items (name, display_name, description, menu_type, parent_menu_id, section_id, url_pattern, icon_class, display_order, is_visible, is_active, requires_permission, badge_text, badge_color) VALUES
-- Main navigation
('main_dashboard', 'Dashboard', 'Main social media dashboard', 'main', NULL, 1, '/syndication/dashboard', 'fas fa-home', 1, true, true, NULL, NULL, NULL),
('main_platforms', 'Platforms', 'Manage social media platforms', 'main', NULL, 2, '/syndication/platforms', 'fas fa-cogs', 2, true, true, NULL, NULL, NULL),
('main_content', 'Content', 'Manage content and posts', 'main', NULL, 3, '/syndication/content', 'fas fa-edit', 3, true, true, NULL, NULL, NULL),

-- Platform submenu
('platform_facebook', 'Facebook', 'Facebook platform settings', 'main', 2, 4, '/syndication/platform-settings/facebook', 'fab fa-facebook', 1, true, true, NULL, 'Active', 'success'),
('platform_instagram', 'Instagram', 'Instagram platform settings', 'main', 2, 4, '/syndication/platform-settings/instagram', 'fab fa-instagram', 2, true, true, NULL, 'Coming Soon', 'warning'),
('platform_twitter', 'Twitter', 'Twitter platform settings', 'main', 2, 4, '/syndication/platform-settings/twitter', 'fab fa-twitter', 3, true, true, NULL, 'Planned', 'info'),

-- Channel submenu for Facebook
('facebook_feed', 'Feed Posts', 'Facebook feed post management', 'main', 4, 5, '/syndication/platform-settings/facebook#feed', 'fas fa-edit', 1, true, true, NULL, NULL, NULL),
('facebook_stories', 'Stories', 'Facebook stories management', 'main', 4, 6, '/syndication/platform-settings/facebook#stories', 'fas fa-mobile-alt', 2, true, true, NULL, NULL, NULL),
('facebook_reels', 'Reels', 'Facebook reels management', 'main', 4, 7, '/syndication/platform-settings/facebook#reels', 'fas fa-video', 3, true, true, NULL, NULL, NULL),
('facebook_groups', 'Groups', 'Facebook groups management', 'main', 4, 8, '/syndication/platform-settings/facebook#groups', 'fas fa-users', 4, true, true, NULL, NULL, NULL);

-- =====================================================
-- 3. SEED UI DISPLAY RULES
-- =====================================================
INSERT INTO ui_display_rules (rule_name, description, rule_type, target_type, target_id, condition_expression, is_active, priority) VALUES
-- Conditional display rules
('show_facebook_analytics', 'Show Facebook analytics only when platform is developed', 'conditional', 'section', 6, '{"condition": "platform_status", "operator": "equals", "value": "developed", "platform": "facebook"}', true, 1),
('hide_coming_soon_platforms', 'Hide platforms that are not yet developed', 'conditional', 'menu_item', 5, '{"condition": "platform_status", "operator": "not_equals", "value": "developed"}', true, 2),
('show_channel_configs', 'Show channel configurations only when platform is active', 'conditional', 'section', 5, '{"condition": "platform_status", "operator": "in", "value": ["active", "developed"]}', true, 3),

-- Permission-based rules
('admin_only_analytics', 'Show analytics only to admin users', 'permission', 'section', 6, '{"permission": "admin", "required": true}', true, 4),
('developer_tools', 'Show developer tools only to developers', 'permission', 'menu_item', 2, '{"permission": "developer", "required": true}', true, 5),

-- Status-based rules
('active_platforms_only', 'Show only active platforms in main menu', 'status', 'menu_item', 2, '{"status": "active", "required": true}', true, 6);

-- =====================================================
-- 4. SEED PRIORITY FACTORS
-- =====================================================
INSERT INTO priority_factors (factor_name, display_name, description, factor_type, weight, calculation_formula, is_active, is_configurable, min_value, max_value, default_value, unit) VALUES
-- Recency factors
('post_recency', 'Post Recency', 'How recently content was posted', 'recency', 0.25, '{"formula": "1 / (days_since_post + 1)", "max_days": 30}', true, true, 0.0, 1.0, 0.25, 'days'),
('engagement_recency', 'Engagement Recency', 'How recently content received engagement', 'recency', 0.20, '{"formula": "1 / (days_since_engagement + 1)", "max_days": 14}', true, true, 0.0, 1.0, 0.20, 'days'),

-- Activity factors
('posting_frequency', 'Posting Frequency', 'How often content is posted', 'activity', 0.15, '{"formula": "posts_last_30_days / 30", "max_posts": 30}', true, true, 0.0, 1.0, 0.15, 'posts/day'),
('api_activity', 'API Activity', 'Recent API calls and interactions', 'activity', 0.10, '{"formula": "api_calls_last_7_days / 100", "max_calls": 100}', true, true, 0.0, 1.0, 0.10, 'calls/day'),

-- Engagement factors
('engagement_rate', 'Engagement Rate', 'Content engagement performance', 'engagement', 0.20, '{"formula": "total_engagement / total_reach", "max_rate": 0.1}', true, true, 0.0, 0.1, 0.05, 'percentage'),
('success_rate', 'Success Rate', 'Successful post delivery rate', 'engagement', 0.10, '{"formula": "successful_posts / total_posts", "max_rate": 1.0}', true, true, 0.0, 1.0, 0.90, 'percentage');

-- =====================================================
-- 5. SEED CONTENT PRIORITIES (calculated examples)
-- =====================================================
INSERT INTO content_priorities (content_type, content_id, priority_score, priority_factors, last_calculated_at, calculation_version) VALUES
-- Facebook platform priority
('platform', 1, 0.875, '{"post_recency": 0.25, "engagement_recency": 0.20, "posting_frequency": 0.15, "api_activity": 0.10, "engagement_rate": 0.20, "success_rate": 0.10}', CURRENT_TIMESTAMP, '1.0'),

-- Facebook channels priorities
('channel', 1, 0.920, '{"post_recency": 0.25, "engagement_recency": 0.20, "posting_frequency": 0.15, "api_activity": 0.10, "engagement_rate": 0.20, "success_rate": 0.10}', CURRENT_TIMESTAMP, '1.0'),
('channel', 2, 0.780, '{"post_recency": 0.20, "engagement_recency": 0.15, "posting_frequency": 0.10, "api_activity": 0.08, "engagement_rate": 0.15, "success_rate": 0.10}', CURRENT_TIMESTAMP, '1.0'),
('channel', 3, 0.650, '{"post_recency": 0.15, "engagement_recency": 0.10, "posting_frequency": 0.08, "api_activity": 0.05, "engagement_rate": 0.12, "success_rate": 0.10}', CURRENT_TIMESTAMP, '1.0'),
('channel', 4, 0.720, '{"post_recency": 0.18, "engagement_recency": 0.12, "posting_frequency": 0.12, "api_activity": 0.08, "engagement_rate": 0.12, "success_rate": 0.10}', CURRENT_TIMESTAMP, '1.0');

-- =====================================================
-- 6. SEED UI USER PREFERENCES (example for user 1)
-- =====================================================
INSERT INTO ui_user_preferences (user_id, preference_key, preference_value, preference_type, category, is_global) VALUES
(1, 'default_collapsed_sections', '["analytics", "advanced_settings"]', 'json', 'ui_behavior', false),
(1, 'theme_preference', 'dark', 'string', 'appearance', false),
(1, 'auto_refresh_interval', '300', 'number', 'ui_behavior', false),
(1, 'show_priority_scores', 'true', 'boolean', 'ui_behavior', false),
(1, 'default_platform', 'facebook', 'string', 'navigation', false),

-- Global preferences (apply to all users)
(1, 'enable_notifications', 'true', 'boolean', 'notifications', true),
(1, 'default_language', 'en', 'string', 'localization', true),
(1, 'timezone', 'UTC', 'string', 'localization', true);

-- =====================================================
-- 7. SEED UI SESSION STATE (example session)
-- =====================================================
INSERT INTO ui_session_state (session_id, user_id, state_key, state_value, state_type, expires_at) VALUES
('session_12345', 1, 'last_visited_platform', 'facebook', 'string', CURRENT_TIMESTAMP + INTERVAL '24 hours'),
('session_12345', 1, 'accordion_state', '{"platform_config": "expanded", "channel_settings": "collapsed"}', 'json', CURRENT_TIMESTAMP + INTERVAL '24 hours'),
('session_12345', 1, 'selected_channel', 'feed_post', 'string', CURRENT_TIMESTAMP + INTERVAL '24 hours'),
('session_12345', 1, 'filter_preferences', '{"show_active_only": true, "sort_by": "priority"}', 'json', CURRENT_TIMESTAMP + INTERVAL '24 hours');

-- =====================================================
-- DATA SEEDING COMPLETE
-- =====================================================
