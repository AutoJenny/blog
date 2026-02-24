ALTER TABLE calendar_week_items
ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;

WITH weeks_without_primary AS (
    SELECT cwi.year, cwi.week_number, MIN(cwi.id) AS primary_id
    FROM calendar_week_items cwi
    WHERE cwi.item_type = 'idea'
      AND cwi.is_active = TRUE
    GROUP BY cwi.year, cwi.week_number
    HAVING SUM(CASE WHEN cwi.is_primary THEN 1 ELSE 0 END) = 0
)
UPDATE calendar_week_items cwi
SET is_primary = TRUE, updated_at = NOW()
FROM weeks_without_primary w
WHERE cwi.id = w.primary_id;

CREATE UNIQUE INDEX IF NOT EXISTS unique_primary_idea_per_week
ON calendar_week_items (year, week_number)
WHERE item_type = 'idea' AND is_primary = TRUE;
