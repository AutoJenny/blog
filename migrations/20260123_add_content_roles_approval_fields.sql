-- Migration: Add approval and validation fields to posting_queue
-- Date: 2026-01-23
-- Purpose: Support Phase 2.5 manual approval and Phase 2.4 validation for Content Roles Framework
-- Notes:
--   - This migration is strictly additive and backwards compatible
--   - All new columns are nullable to support existing rows

BEGIN;

-- Add approval fields
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS approved_by VARCHAR(100);

-- Add validation report field (JSONB for structured validation results)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS validation_report_json JSONB;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_posting_queue_approved 
ON posting_queue(approved_at) 
WHERE approved_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_posting_queue_status_role 
ON posting_queue(status, role) 
WHERE role IS NOT NULL;

-- Add comments
COMMENT ON COLUMN posting_queue.approved_at IS 'Timestamp when post was manually approved for scheduling';
COMMENT ON COLUMN posting_queue.approved_by IS 'User identifier who approved the post';
COMMENT ON COLUMN posting_queue.validation_report_json IS 'Structured validation results (JSON) including checks, issues, word count, etc.';

COMMIT;
