import re
import sys

SCHEMA_FILE = 'create_tables.sql'
DUMP_FILE = 'blog_data_only_20250528.sql'
OUTPUT_FILE = 'blog_data_only_20250528_transformed.sql'

# --- 1. Parse schema ---
def parse_schema(schema_file):
    table_columns = {}
    current_table = None
    columns = []
    with open(schema_file, 'r') as f:
        for line in f:
            m = re.match(r'CREATE TABLE (IF NOT EXISTS )?"?([a-zA-Z0-9_]+)"? \(', line)
            if m:
                if current_table and columns:
                    table_columns[current_table] = columns
                current_table = m.group(2)
                columns = []
            elif current_table:
                if line.strip().startswith(')'):
                    if current_table and columns:
                        table_columns[current_table] = columns
                    current_table = None
                    columns = []
                else:
                    col_match = re.match(r'\s*"?([a-zA-Z0-9_]+)"? ', line)
                    if col_match:
                        columns.append(col_match.group(1))
    return table_columns

# --- 2. Parse and transform dump ---
def transform_dump(dump_file, table_columns, output_file):
    with open(dump_file, 'r') as f:
        lines = f.readlines()
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'COPY public\.([a-zA-Z0-9_]+) \(([^)]+)\) FROM stdin;', line)
        if m:
            table = m.group(1)
            dump_cols = [c.strip() for c in m.group(2).split(',')]
            schema_cols = table_columns.get(table)
            if not schema_cols:
                print(f"Skipping table {table} (not in schema)")
                # Skip to next \. line
                i += 1
                while i < len(lines) and lines[i].strip() != '\.':
                    i += 1
                i += 1
                continue
            out_lines.append(f'COPY public.{table} ({', '.join(schema_cols)}) FROM stdin;\n')
            i += 1
            # Transform data rows
            while i < len(lines) and lines[i].strip() != '\.':
                row = lines[i].rstrip('\n')
                if not row.strip():
                    i += 1
                    continue
                parts = row.split('\t')
                row_dict = {col: (parts[idx] if idx < len(parts) else '\\N') for idx, col in enumerate(dump_cols)}
                new_row = []
                for col in schema_cols:
                    new_row.append(row_dict.get(col, '\\N'))
                out_lines.append('\t'.join(new_row) + '\n')
                i += 1
            out_lines.append('\\.\n')
            i += 1
        else:
            out_lines.append(line)
            i += 1
    with open(output_file, 'w') as f:
        f.writelines(out_lines)
    print(f"Transformed dump written to {output_file}")

if __name__ == '__main__':
    table_columns = parse_schema(SCHEMA_FILE)
    transform_dump(DUMP_FILE, table_columns, OUTPUT_FILE) 