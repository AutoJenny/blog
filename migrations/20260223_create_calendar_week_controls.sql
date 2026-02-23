-- Migration: Create calendar_week_controls table (W2-FIX-9.2)
-- Purpose: Week-level automation controls (automation_enabled, locked)
-- Date: 2026-02-23

BEGIN;

CREATE TABLE IF NOT EXISTS calendar_week_controls (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 53),
    automation_enabled BOOLEAN DEFAULT TRUE,
    locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (year, week_number)
);

CREATE INDEX IF NOT EXISTS idx_calendar_week_controls_week
    ON calendar_week_controls(year, week_number);

COMMENT ON TABLE calendar_week_controls IS 'W2-FIX-9.2: Week-level automation controls. automation_enabled: allow automation for this week. locked: prevent automation from modifying posts.';
COMMENT ON COLUMN calendar_week_controls.automation_enabled IS 'If false, automation skips this week silently';
COMMENT ON COLUMN calendar_week_controls.locked IS 'If true, automation must not modify posts for this week (409 week_locked)';

COMMIT;
