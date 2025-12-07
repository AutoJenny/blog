#!/usr/bin/env python3
"""
Generate condensed legacy histories from OpenAI fact-checked narratives.

For each family that:
  - has research_data.metadata.narrative_fact_checked
  - does NOT already have a family_resources row with
        resource_type = 'text'
        resource_category = 'history_legacy_generated'

this script:
  - asks the LLM to produce a short, purely factual summary
    (~400 characters), with:
      * no introduction
      * no conclusions
      * no commentary or meta-text
      * no headings
  - stores the result as a new text resource with
        resource_category = 'history_legacy_generated'

Usage:
    python3 scripts/generate_legacy_from_openai.py [--limit N] [--start-from ID] [--dry-run]
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
from config.unified_config import get_config

# Import LLM service
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
    from app.llm.services import LLMService
except ImportError:
    try:
        from blueprints.planning_llm import LLMService
    except ImportError:
        LLMService = None


def get_families_with_openai_narrative(limit: Optional[int] = None,
                                       start_from: Optional[int] = None):
    """Fetch families that have an OpenAI fact-checked narrative but no generated legacy."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            where_clauses = [
                "f.research_data IS NOT NULL",
                "f.research_data ? 'metadata'",
                "f.research_data->'metadata' ? 'narrative_fact_checked'",
                # No existing generated legacy history for this family
                "NOT EXISTS ("
                "   SELECT 1 FROM family_resources fr "
                "   WHERE fr.family_id = f.id "
                "     AND fr.resource_type = 'text' "
                "     AND fr.resource_category = 'history_legacy_generated'"
                ")",
            ]

            params = []
            if start_from is not None:
                where_clauses.append("f.id >= %s")
                params.append(start_from)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT
                    f.id,
                    f.name,
                    f.research_data->'metadata'->>'narrative_fact_checked' AS narrative
                FROM families f
                WHERE {where_sql}
                ORDER BY f.id
            """
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)

            cur.execute(query, params)
            return cur.fetchall()


def build_summary_prompt(family_name: str, narrative_html: str) -> str:
    """Build a strict prompt asking for a concise factual summary (~2–3 sentences)."""
    prompt = f"""You are a precise historical summariser.

You will be given a fact-checked HTML narrative about the surname/family "{family_name}".

Your task:
- Write a SINGLE BLOCK of factual prose (no headings, no lists).
- Length target: about 2–3 sentences, ideally between 250 and 600 characters.
- Use only facts from the narrative.
- NO introduction phrases (e.g. "This summary...", "In summary...", "This narrative...").
- NO conclusions or commentary (e.g. "Overall...", "In conclusion...").
- NO meta-commentary about the text or your process.
- NO headings, no <h3>, no HTML tags at all.
- UK English spelling.

Content:
- State only concrete, documented facts about the family: origins, regions, periods, key roles or themes.
- Use plain sentences separated by full stops.

Output:
- Plain text only.
- ONE paragraph.
- Around 2–3 sentences with dense factual content.

Here is the narrative to summarise:
<<<
{narrative_html}
>>>

Now produce the summary as specified."""
    return prompt


def generate_summary(llm_service, family_name: str, narrative_html: str) -> Optional[str]:
    """Call the local LLM to generate a condensed factual summary (no OpenAI required)."""
    prompt = build_summary_prompt(family_name, narrative_html)
    try:
        response = None

        # Preferred path: blog-core LLMService with .generate using Ollama
        if hasattr(llm_service, "generate"):
            response = llm_service.generate(
                prompt=prompt,
                model_name=os.environ.get("DEFAULT_LLM_MODEL", "mistral"),
                temperature=0.2,
                max_tokens=300,
            )
        # Fallback: planning_llm LLMService with execute_llm_request using Ollama chat API
        elif hasattr(llm_service, "execute_llm_request"):
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
            result = llm_service.execute_llm_request(
                provider="ollama",
                model="llama3.2",
                messages=messages,
                max_tokens=300,
                temperature=0.2,
            )
            if "error" in result:
                print(f"  Error from LLM service: {result['error']}")
                return None
            response = result.get("content", "")
        else:
            print("  Error: LLMService interface not supported")
            return None

        summary = (response or "").strip()
        if not summary:
            print("  Warning: empty summary from LLM")
            return None

        # Do NOT hard-trim; rely on prompt to keep around ~400 characters.
        # Just normalise whitespace a bit.
        import re as _re
        summary = _re.sub(r'\s+', ' ', summary).strip()

        return summary
    except Exception as e:
        print(f"  Error during LLM summarisation: {e}")
        return None


def save_legacy_generated(family_id: int, summary: str, dry_run: bool = False):
    """Save the generated summary into family_resources as history_legacy_generated."""
    if dry_run:
        print(f"  [DRY RUN] Would save history_legacy_generated (length {len(summary)} chars)")
        return

    metadata = {
        "source": "openai_summary_from_narrative_fact_checked",
        "max_chars": 400,
        "created_from": "narrative_fact_checked",
    }

    import json

    metadata_json = json.dumps(metadata)

    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO family_resources (
                    family_id,
                    resource_type,
                    resource_category,
                    resource_value,
                    resource_metadata
                )
                VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (
                    family_id,
                    "text",
                    "history_legacy_generated",
                    summary,
                    metadata_json,
                ),
            )
        conn.commit()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate condensed legacy histories from OpenAI narratives"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of families to process (for testing)",
    )
    parser.add_argument(
        "--start-from", type=int, help="Start from family ID (inclusive)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing to the database",
    )

    args = parser.parse_args()

    if LLMService is None:
        print("Error: LLMService could not be imported. Cannot generate summaries.")
        sys.exit(1)

    # LLMService reads configuration from environment; no config object needed
    llm_service = LLMService()

    families = get_families_with_openai_narrative(
        limit=args.limit, start_from=args.start_from
    )

    total = len(families)
    print("\n" + "=" * 60)
    print("Generate legacy histories from OpenAI narratives")
    print("=" * 60)
    print(f"Families to process: {total}")
    print(f"Dry run: {args.dry_run}")
    print()

    success = 0
    skipped = 0
    failed = 0

    for i, row in enumerate(families, 1):
        family_id = row["id"]
        family_name = row["name"]
        narrative = row["narrative"] or ""

        print(f"[{i}/{total}] {family_name} (ID: {family_id})")

        if not narrative.strip():
            print("  Skipping: narrative_fact_checked is empty")
            skipped += 1
            continue

        summary = generate_summary(llm_service, family_name, narrative)
        if not summary:
            print("  ✗ Failed to generate summary")
            failed += 1
            continue

        print(f"  ✓ Generated summary ({len(summary)} chars)")
        save_legacy_generated(family_id, summary, dry_run=args.dry_run)
        success += 1

    print("\n" + "=" * 60)
    print("Generation complete")
    print("=" * 60)
    print(f"Total families considered: {total}")
    print(f"Summaries generated: {success}")
    print(f"Skipped (no narrative): {skipped}")
    print(f"Failed: {failed}")

    return 0


if __name__ == "__main__":
    sys.exit(main())


