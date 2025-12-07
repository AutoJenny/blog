#!/usr/bin/env python3
"""\
Review and repair <blockquote> elements in fact-checked historical narratives.

This script processes all families flagged in the blockquote audit that need review.
For each family:
- Fetches the full HTML fact-checked narrative from the DB
- Sends that HTML to OpenAI with strict instructions to adjust <blockquote> elements only
- Saves the revised HTML back to the database (unless --dry-run is used)

Usage:
    python3 scripts/review_blockquotes_openai.py [--dry-run] [--limit N] [--start-from ID]

Requirements:
    - OPENAI_API_KEY must be set in the environment.
    - The `openai` Python package must be installed (v1.x preferred).
"""

import os
import sys
import json
import time
from typing import Optional, List, Dict

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.database import db_manager


def load_families_needing_review() -> List[Dict]:
    """Load all families needing review from the blockquote audit JSON."""
    path = os.path.join("data", "blockquote_audit_results.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    families = data.get("families", [])
    # Filter to only those that need review
    return [f for f in families if f.get("needs_review", False)]


def get_fact_checked_narrative(family_id: int) -> Optional[tuple]:
    """Fetch the full fact-checked narrative HTML from the DB for a family."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    name,
                    research_data->'metadata'->>'narrative_fact_checked' AS narrative
                FROM families
                WHERE id = %s
                """,
                (family_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row["name"], row["narrative"]


def save_revised_narrative(family_id: int, revised_html: str, dry_run: bool = False):
    """Save the revised narrative back to the database."""
    if dry_run:
        return
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Update the narrative_fact_checked in research_data
            cur.execute(
                """
                UPDATE families
                SET research_data = jsonb_set(
                    COALESCE(research_data, '{}'::jsonb),
                    '{metadata,narrative_fact_checked}',
                    %s::jsonb
                )
                WHERE id = %s
                """,
                (json.dumps(revised_html), family_id),
            )
        conn.commit()


def build_openai_prompt(family_name: str, html: str) -> str:
    """Build the instructions for OpenAI to repair blockquote usage only."""
    instructions = f"""You are editing a *fact-checked historical narrative* for the surname / family "{family_name}".

You are given the narrative as HTML. Your job is to review and, if needed, correct the use of <blockquote> elements ONLY.

CRITICAL RULES:
- The overall narrative is already fact-checked and should NOT be substantially rewritten.
- You may edit, add, or remove <blockquote> elements and their immediate context, but you MUST preserve the core narrative structure and factual content.

INTENDED USE OF <blockquote>:
- Each <blockquote> should ideally contain an authentic historical quotation relevant to the family.
  PREFERRED TYPES (in order of preference):
  1. **Family/clan mottos** (e.g., "Per mare per terras" or "Touch not the cat but a glove")
  2. **Famous quotes by notable family members** (spoken words, written statements, or recorded sayings by historical figures from this family)
  3. **Quotations from historical documents, charters, letters, poems, or ballads** that are actually about this family or its notable members
  4. **Contemporary historical descriptions** of the family or its members from period sources
- <blockquote> must NOT be used for:
  - General narrative or explanatory text
  - Modern summary prose
  - Placeholder text (e.g. "[Insert the actual quoted verse here]")
  - Generic inspirational or marketing-style lines
  - Heraldic descriptions (unless they are quoted from a historical source)

YOUR TASK:
1. Carefully inspect every <blockquote> in the HTML.
2. For each existing blockquote:
   - If it clearly is *not* an authentic historical quotation, try to replace it with a genuine quotation about the family or its noted members.
   - **PRIORITIZE**: Family/clan mottos or famous quotes by notable family members. These are the most valuable and authentic types of quotations.
   - You may perform background web research to identify a short, suitable historical quotation, motto, or famous quote.
   - If you cannot find a suitable quotation that you are reasonably confident is authentic and relevant, REMOVE the <blockquote> and rewrite the surrounding text so the narrative reads smoothly without it.
3. If the narrative has *no* genuine quotations at all but you can find one or two strong, authentic historical quotations (especially mottos or quotes by family members), you may insert them in appropriate places using <blockquote>.
4. Keep quotations short and precise. Do not invent sources; use only quotes you believe are genuinely attested in historical sources.
5. Do NOT add editorial commentary like "this quote shows"; keep the tone factual and consistent with the existing narrative.

OUTPUT FORMAT:
- Return ONLY the full revised HTML for the narrative.
- Do NOT wrap your answer in markdown or backticks.
- Do NOT prepend explanations, notes or commentary.
- The output should be a complete HTML fragment that can directly replace the existing narrative_fact_checked field.

Here is the current narrative HTML to edit:

<<<HTML
{html}
>>>HTML

Now return the fully revised HTML with corrected <blockquote> usage as described above."""
    return instructions


def call_openai_edit(html: str, family_name: str) -> str:
    """Call OpenAI to revise blockquotes in the given HTML."""
    from openai import OpenAI  # type: ignore

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

    client = OpenAI(api_key=api_key)

    prompt = build_openai_prompt(family_name, html)

    # Use a reasonably small, cost-effective model by default
    model = os.environ.get("OPENAI_MODEL_BLOCKQUOTE_REVIEW", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a careful historical editor working on HTML narratives."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4000,
    )

    content = resp.choices[0].message.content or ""
    return content.strip()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Review and repair blockquotes in OpenAI narratives")
    parser.add_argument("--dry-run", action="store_true", help="Do not save changes to database")
    parser.add_argument("--limit", type=int, help="Limit number of families to process (for testing)")
    parser.add_argument("--start-from", type=int, help="Start from family ID (inclusive)")
    parser.add_argument("--skip", type=int, default=0, help="Skip first N families (for resuming)")

    args = parser.parse_args()

    families = load_families_needing_review()
    
    # Store original total before filtering
    original_total = len(families)
    
    # Apply filters
    if args.start_from:
        families = [f for f in families if f["family_id"] >= args.start_from]
    
    # Skip already processed families
    if args.skip > 0:
        families = families[args.skip:]
    
    if args.limit:
        families = families[:args.limit]
    
    total = len(families)
    
    if total == 0:
        print("No families found needing review.")
        return 0

    print("\n" + "=" * 80)
    print("Review and repair blockquotes in OpenAI narratives")
    print("=" * 80)
    print(f"Families to process: {total} (out of {original_total + args.skip} total)")
    if args.skip > 0:
        print(f"Resuming from position {args.skip + 1}")
    print(f"Dry run: {args.dry_run}")
    print()

    success = 0
    failed = 0
    skipped = 0

    for i, family_data in enumerate(families, 1):
        family_id = family_data["family_id"]
        family_name = family_data["family_name"]
        
        # Display actual position including skipped families
        actual_position = i + args.skip
        print(f"[{actual_position}/{total + args.skip}] Processing: {family_name} (ID: {family_id})")
        
        result = get_fact_checked_narrative(family_id)
        if not result:
            print(f"  ✗ No narrative_fact_checked found")
            skipped += 1
            continue
        
        name, html = result
        
        if not html or not html.strip():
            print(f"  ✗ Empty narrative")
            skipped += 1
            continue
        
        try:
            print(f"  Calling OpenAI...")
            revised_html = call_openai_edit(html, family_name)
            
            if not revised_html or not revised_html.strip():
                print(f"  ✗ Empty response from OpenAI")
                failed += 1
                continue
            
            print(f"  ✓ Received revised HTML ({len(revised_html)} chars)")
            
            save_revised_narrative(family_id, revised_html, dry_run=args.dry_run)
            
            if args.dry_run:
                print(f"  [DRY RUN] Would save to database")
            else:
                print(f"  ✓ Saved to database")
            
            success += 1
            
            # Small delay to avoid rate limiting
            if i < total:
                time.sleep(1)
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
            continue

    print("\n" + "=" * 80)
    print("Processing complete")
    print("=" * 80)
    print(f"Total families processed: {total}")
    print(f"Successfully revised: {success}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    if args.dry_run:
        print("\nNOTE: This was a dry run. No changes were saved to the database.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
