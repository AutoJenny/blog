-- Migration: Create matrix_run_ledger table
-- Date: 2026-02-01
-- Purpose: Phase G-1 — Audit trail for matrix pre-generation runs. One row per platform per run.
-- Notes:
--   - Written by scripts/pregenerate_matrix.py at run start (status 'running') and at completion (finished_at, status, report_path).
--   - No foreign keys. No indexes beyond PK. status: 'running' | 'success' | 'partial' | 'failed'.

BEGIN;

CREATE TABLE IF NOT EXISTS matrix_run_ledger (
    id SERIAL PRIMARY KEY,
    platform TEXT NOT NULL,
    start_date DATE NOT NULL,
    weeks_ahead INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    report_path TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE matrix_run_ledger IS 'Phase G-1: One row per platform per matrix run; audit trail for calendar population.';
COMMENT ON COLUMN matrix_run_ledger.platform IS 'facebook | instagram';
COMMENT ON COLUMN matrix_run_ledger.status IS 'running (in progress) | success | partial | failed';

COMMIT;
