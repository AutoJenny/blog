# W2 Stage migrations proof (1.1 + 1.2)

## 1.1 Add early-stage column on post

### Commands

```bash
psql -d blog -f migrations/20260226_add_workflow_stage_column.sql
```

```
psql:migrations/20260226_add_workflow_stage_column.sql:7: NOTICE:  column "workflow_stage" of relation "post" already exists, skipping
ALTER TABLE
UPDATE 0
ALTER TABLE
ALTER TABLE
```

```bash
psql -d blog -c "\d post"
```

(Excerpt — workflow_stage row and check constraint:)

```
 workflow_stage                       | text                        |           | not null | 'metadata'::text
...
Check constraints:
    ...
    "post_workflow_stage_valid" CHECK (workflow_stage = ANY (ARRAY['metadata'::text, 'ideas'::text, 'structure'::text, 'titling'::text, 'authoring'::text, 'imaging'::text, 'review'::text]))
```

```bash
psql -d blog -c "SELECT column_name, column_default, is_nullable FROM information_schema.columns WHERE table_name='post' AND column_name='workflow_stage';"
```

```
  column_name   |  column_default  | is_nullable 
----------------+------------------+-------------
 workflow_stage | 'metadata'::text | NO
(1 row)
```

```bash
psql -d blog -c "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='post'::regclass AND contype='c';"
```

```
             conname              | pg_get_constraintdef
----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 ...
 post_workflow_stage_valid        | CHECK ((workflow_stage = ANY (ARRAY['metadata'::text, 'ideas'::text, 'structure'::text, 'titling'::text, 'authoring'::text, 'imaging'::text, 'review'::text])))
(4 rows)
```

**Required DB outcome:** Column `post.workflow_stage` TEXT NOT NULL DEFAULT 'metadata'. CHECK includes exactly: metadata, ideas, structure, titling, authoring, imaging, review. Verified.

---

## 1.2 Create required-ideas table

### Commands

```bash
psql -d blog -f migrations/20260226_create_post_required_idea.sql
```

```
psql:migrations/20260226_create_post_required_idea.sql:10: NOTICE:  relation "post_required_idea" already exists, skipping
CREATE TABLE
...
CREATE INDEX
```

```bash
psql -d blog -c "\d post_required_idea"
```

```
                                       Table "public.post_required_idea"
   Column   |           Type           | Collation | Nullable |                    Default                     
------------+--------------------------+-----------+----------+------------------------------------------------
 id         | integer                  |           | not null | nextval('post_required_idea_id_seq'::regclass)
 post_id    | integer                  |           | not null | 
 text       | text                     |           | not null | 
 sort_order | integer                  |           | not null | 0
 created_at | timestamp with time zone |           |          | now()
Indexes:
    "post_required_idea_pkey" PRIMARY KEY, btree (id)
    "idx_post_required_idea_post_id" btree (post_id)
Foreign-key constraints:
    "post_required_idea_post_id_fkey" FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE
```

**Required DB outcome:** Table exists with id, post_id, text, sort_order, created_at. Verified.

---

## Proof block

```
git rev-parse HEAD
git status
git log -1 --oneline
```

(To be filled after commits.)
