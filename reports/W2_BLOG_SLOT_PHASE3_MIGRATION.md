# W2 Blog Slot Phase 3 — Migration Report

## Commands run

```bash
psql -d blog -f migrations/20260225_add_blog_item_type.sql
psql -d blog -c "\d calendar_week_items"
```

## Migration output

```
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
```

## \d calendar_week_items (relevant parts)

- **item_type check:** `calendar_week_items_item_type_check1` now includes `'blog'` in the allowed list.
- **valid_weekday:** `blog` is included in the week-level list (weekday must be NULL) with theme, weekly_word, weekly_phrase.
- **item_id:** NOT NULL — blog slot will use `item_id = 0` (one row per week, unique on (year, week_number, item_type, item_id)).

Full constraint excerpts:

- `calendar_week_items_item_type_check1` CHECK (item_type = ANY (ARRAY['theme', 'idea', 'annual_event', 'special_event', 'recipe', 'profile', 'weekly_word', 'weekly_phrase', 'syndication', 'blog']))
- `valid_weekday` CHECK ((item_type = ANY (ARRAY['theme', 'weekly_word', 'weekly_phrase', 'blog']) AND weekday IS NULL) OR ...)
