# W2 Phase 3.1 — Required ideas schema upgrade (post_required_idea)

Migration: `migrations/20260226_post_required_idea_metadata.sql`

```sql
ALTER TABLE post_required_idea
  ADD COLUMN IF NOT EXISTS category TEXT,
  ADD COLUMN IF NOT EXISTS rationale TEXT,
  ADD COLUMN IF NOT EXISTS source_urls JSONB,
  ADD COLUMN IF NOT EXISTS rank INT,
  ADD COLUMN IF NOT EXISTS is_selected BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS created_by TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_post_required_idea_post_id_selected
  ON post_required_idea(post_id, is_selected);

CREATE INDEX IF NOT EXISTS idx_post_required_idea_post_id_category
  ON post_required_idea(post_id, category);
```

Migration run:

```bash
psql -d blog -f migrations/20260226_post_required_idea_metadata.sql
```

Output:

```text
ALTER TABLE
CREATE INDEX
CREATE INDEX
```

---

## \d post_required_idea

```text
                                       Table "public.post_required_idea"
   Column    |           Type           | Collation | Nullable |                    Default                     
-------------+--------------------------+-----------+----------+------------------------------------------------
 id          | integer                  |           | not null | nextval('post_required_idea_id_seq'::regclass)
 post_id     | integer                  |           | not null | 
 text        | text                     |           | not null | 
 sort_order  | integer                  |           | not null | 0
 created_at  | timestamp with time zone |           |          | now()
 category    | text                     |           |          | 
 rationale   | text                     |           |          | 
 source_urls | jsonb                    |           |          | 
 rank        | integer                  |           |          | 
 is_selected | boolean                  |           | not null | true
 created_by  | text                     |           |          | 
 updated_at  | timestamp with time zone |           | not null | now()
Indexes:
    "post_required_idea_pkey" PRIMARY KEY, btree (id)
    "idx_post_required_idea_post_id" btree (post_id)
    "idx_post_required_idea_post_id_category" btree (post_id, category)
    "idx_post_required_idea_post_id_selected" btree (post_id, is_selected)
Foreign-key constraints:
    "post_required_idea_post_id_fkey" FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE
```

---

## information_schema columns

Command:

```bash
psql -d blog -c "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='post_required_idea' ORDER BY ordinal_position;"
```

Output:

```text
 column_name |        data_type         | is_nullable |                 column_default                 
-------------+--------------------------+-------------+------------------------------------------------
 id          | integer                  | NO          | nextval('post_required_idea_id_seq'::regclass)
 post_id     | integer                  | NO          | 
 text        | text                     | NO          | 
 sort_order  | integer                  | NO          | 0
 created_at  | timestamp with time zone | YES         | now()
 category    | text                     | YES         | 
 rationale   | text                     | YES         | 
 source_urls | jsonb                    | YES         | 
 rank        | integer                  | YES         | 
 is_selected | boolean                  | NO          | true
 created_by  | text                     | YES         | 
 updated_at  | timestamp with time zone | NO          | now()
(12 rows)
```

---

## Index list

Command:

```bash
psql -d blog -c "\\di+ post_required_idea*"
```

Output:

```text
                                                       List of relations
 Schema |          Name           | Type  |   Owner   |       Table        | Persistence | Access method | Size  | Description 
--------+-------------------------+-------+-----------+--------------------+-------------+---------------+-------+-------------
 public | post_required_idea_pkey | index | autojenny | post_required_idea | permanent   | btree         | 16 kB | 
(1 row)
```

