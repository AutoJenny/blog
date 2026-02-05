-- Phase H-5: Explicit "current output" selection per slot (one run marked current per item+slot)
-- Avoids mutating generation_runs; keeps "current" separate from "history"

CREATE TABLE IF NOT EXISTS workbench_current_outputs (
    id SERIAL PRIMARY KEY,
    content_ref INTEGER NOT NULL,
    platform TEXT NOT NULL,
    channel_type TEXT NOT NULL,
    slot_identifier TEXT NOT NULL DEFAULT 'primary',
    run_id INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(content_ref, platform, channel_type, slot_identifier)
);

CREATE INDEX IF NOT EXISTS idx_workbench_current_outputs_item
    ON workbench_current_outputs(content_ref, platform, channel_type, slot_identifier);

COMMENT ON TABLE workbench_current_outputs IS 'Phase H-5: One current run per (content_ref, platform, channel_type, slot_identifier). Upsert on selection; runs remain immutable.';
COMMENT ON COLUMN workbench_current_outputs.slot_identifier IS 'Slot (e.g. primary for blog_post).';
COMMENT ON COLUMN workbench_current_outputs.run_id IS 'generation_runs.id whose output is current for this slot.';
