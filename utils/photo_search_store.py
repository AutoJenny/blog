"""
Photo Search Persistence Utilities

Small helpers to persist photo search results and search terms to the
post_section table, keeping SQL out of the blueprint.
"""

import json
from typing import List, Dict


def store_photo_search_results(conn, *, post_id: int, section_id: int,
                               results: List[Dict], search_term: str) -> None:
    """
    Persist search results and append the search term to image_search_terms.

    NOTE: We intentionally avoid touching updated_at to be compatible with
    existing schemas which may not include that column.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE post_section
            SET photo_search_results = %s::jsonb,
                image_search_terms = COALESCE(
                    CASE 
                        WHEN image_search_terms IS NULL THEN '[]'::jsonb
                        ELSE image_search_terms
                    END || %s::jsonb,
                    '[]'::jsonb || %s::jsonb
                )
            WHERE id = %s AND post_id = %s
            RETURNING id
            """,
            (
                json.dumps(results),
                json.dumps([search_term]),
                json.dumps([search_term]),
                section_id,
                post_id,
            ),
        )

        if not cursor.fetchone():
            raise RuntimeError("Failed to save search results")

    conn.commit()


