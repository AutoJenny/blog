#!/usr/bin/env python3
"""
Export OpenAI narratives to CSV, but only for families that do NOT have
existing clan histories (history_legacy, history_scottish, etc.)
"""

import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager

def main():
    output_file = 'data/openai_narratives_no_clan_export.csv'
    
    print("Exporting OpenAI narratives (families WITHOUT existing clan histories)...")
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Query for families with OpenAI narratives but NO clan histories
            cur.execute("""
                SELECT 
                    f.id,
                    f.name,
                    f.research_data->'metadata'->>'narrative_fact_checked' as narrative_fact_checked,
                    (
                        SELECT fr.resource_value
                        FROM family_resources fr
                        WHERE fr.family_id = f.id
                          AND fr.resource_type = 'text'
                          AND fr.resource_category = 'history_legacy_generated'
                        LIMIT 1
                    ) as history_legacy_generated
                FROM families f
                WHERE f.research_data IS NOT NULL
                  AND f.research_data ? 'metadata'
                  AND f.research_data->'metadata' ? 'narrative_fact_checked'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM family_resources fr
                      WHERE fr.family_id = f.id
                        AND fr.resource_type = 'text'
                        AND fr.resource_category IN ('history_legacy', 'history_scottish', 'history_english', 'history_welsh', 'history_irish')
                        AND LENGTH(fr.resource_value) > 10
                  )
                ORDER BY f.name
            """)
            
            families = cur.fetchall()
            
            print(f"Found {len(families)} families with OpenAI narratives but no clan histories")
            
            # Write to CSV
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Record ID',
                    'Family Name',
                    'Fact-Checked Historical Narrative',
                    'History Legacy Generated'
                ])
                
                # Write data
                for row in families:
                    writer.writerow([
                        row['id'],
                        row['name'],
                        row['narrative_fact_checked'] or '',
                        row['history_legacy_generated'] or ''
                    ])
            
            print(f"\nExport complete!")
            print(f"Output file: {output_file}")
            print(f"Total families exported: {len(families)}")
            
            return 0

if __name__ == '__main__':
    sys.exit(main())

