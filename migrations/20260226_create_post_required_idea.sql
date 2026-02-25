-- Instruction Set 8.2: Required ideas stored in dedicated table.
-- Min 3, soft max 12. Enforced on stage advance (ideas -> structure).

CREATE TABLE IF NOT EXISTS post_required_idea (
  id SERIAL PRIMARY KEY,
  post_id INT NOT NULL REFERENCES post(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_required_idea_post_id ON post_required_idea(post_id);
