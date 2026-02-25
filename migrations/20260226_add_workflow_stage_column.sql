-- Instruction Set 8: Explicit workflow_stage column for early development round.
-- Allowed: metadata, ideas, structure, titling, authoring, imaging, review.
-- No auto-advance; stage only changes on explicit "Advance Stage" action.

-- Add column (idempotent for PostgreSQL 9.5+)
ALTER TABLE post
ADD COLUMN IF NOT EXISTS workflow_stage TEXT NOT NULL DEFAULT 'metadata';

-- Ensure no nulls
UPDATE post SET workflow_stage = 'metadata' WHERE workflow_stage IS NULL OR workflow_stage = '';

-- Constraint (drop first to allow re-run)
ALTER TABLE post DROP CONSTRAINT IF EXISTS post_workflow_stage_valid;

ALTER TABLE post
ADD CONSTRAINT post_workflow_stage_valid
CHECK (workflow_stage IN (
  'metadata',
  'ideas',
  'structure',
  'titling',
  'authoring',
  'imaging',
  'review'
));
