import os
import psycopg2
import json
import sys
from app.blog.fields import WORKFLOW_FIELDS

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")

def get_table_columns(table_name):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return columns

def main():
    dev_fields = set(get_table_columns("post_development"))
    section_fields = set(get_table_columns("post_section"))
    result = {}
    warnings = []
    for stage, fields in WORKFLOW_FIELDS.items():
        valid = []
        for f in fields:
            if f in dev_fields or f in section_fields:
                valid.append(f)
            else:
                warnings.append(f"Field '{f}' in '{stage}' not found in DB.")
        result[stage] = valid
    # Warn about DB fields not in mapping
    all_mapped = set(sum(WORKFLOW_FIELDS.values(), []))
    for f in dev_fields.union(section_fields):
        if f not in all_mapped and not f.startswith('id') and not f.endswith('_id'):
            warnings.append(f"DB field '{f}' not in WORKFLOW_FIELDS mapping.")
    print(json.dumps(result, indent=2))
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(w)

if __name__ == "__main__":
    main() 