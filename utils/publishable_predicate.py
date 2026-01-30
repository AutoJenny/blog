"""
Shared definition of "publishable" for executor, hotfix, and cleanup.

Publishable = status in ('ready','pending') and scheduled time has passed.
Used by: scheduled_posting_executor (get_due_posts), hotfix_cancel_surplus_today, cleanup_surplus_daily_posts.

Claim-eligible = publishable AND platform_post_id IS NULL (so we don't claim already-published rows).
"""

# Statuses that count as "publishable" (due for publishing) — must match executor's due-post query
PUBLISHABLE_STATUSES = ('ready', 'pending')

# SQL fragment: scheduled time has passed. Params: (now, now).
# Use with: status IN %(statuses)s AND (this fragment)
SCHEDULED_DUE_FRAGMENT = """
    (
        (scheduled_timestamp IS NOT NULL AND scheduled_timestamp <= %s)
        OR (scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL
            AND (scheduled_date::date + scheduled_time::time)::timestamp <= %s)
    )
"""

# SQL fragment for claim-before-publish: row is still eligible to be claimed.
# Params: (queue_id,). Ensures only one process can claim the row.
# Full claim: UPDATE ... SET status='publishing' WHERE id=%s AND status IN ('ready','pending') AND platform_post_id IS NULL
CLAIM_ELIGIBLE_WHERE = "id = %s AND status IN ('ready', 'pending') AND (platform_post_id IS NULL OR platform_post_id = '')"
