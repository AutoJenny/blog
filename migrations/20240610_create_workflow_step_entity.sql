CREATE TABLE IF NOT EXISTS workflow_step_entity (
    id SERIAL PRIMARY KEY,
    sub_stage_id INTEGER REFERENCES workflow_sub_stage_entity(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    step_order INTEGER NOT NULL,
    UNIQUE(sub_stage_id, name)
); 