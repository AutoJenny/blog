import re

SCHEMA_FILE = 'create_tables.sql'
DUMP_FILE = 'blog_data_only_20250528.sql'
OUTPUT_FILE = 'blog_llm_tables_only.sql'
LLM_TABLES = ['llm_provider', 'llm_model', 'llm_prompt', 'llm_action']

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

def clean_copy_block(table, dump_cols, schema_cols, data_lines):
    out = []
    for line in data_lines:
        if line.strip() == '\\.':
            out.append('\\.')
            break
        parts = line.rstrip('\n').split('\t')
        if len(parts) != len(dump_cols):
            print(f"Skipping malformed row in {table}: {line.strip()}")
            continue
        row_dict = {col: (parts[idx] if idx < len(parts) else '\\N') for idx, col in enumerate(dump_cols)}
        new_row = [row_dict.get(col, '\\N') for col in schema_cols]
        out.append('\t'.join(new_row))
    return out

def main():
    table_columns = parse_schema(SCHEMA_FILE)
    with open(DUMP_FILE, 'r') as f:
        lines = f.readlines()
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'COPY public\.([a-zA-Z0-9_]+) \(([^)]+)\) FROM stdin;', line)
        if m:
            table = m.group(1)
            if table not in LLM_TABLES:
                # Skip to next \. line
                i += 1
                while i < len(lines) and lines[i].strip() != '\.':
                    i += 1
                i += 1
                continue
            dump_cols = [c.strip() for c in m.group(2).split(',')]
            schema_cols = table_columns.get(table)
            if not schema_cols:
                print(f"Skipping table {table} (not in schema)")
                i += 1
                while i < len(lines) and lines[i].strip() != '\.':
                    i += 1
                i += 1
                continue
            out_lines.append(f'COPY public.{table} ({', '.join(schema_cols)}) FROM stdin;\n')
            i += 1
            data_lines = []
            while i < len(lines) and lines[i].strip() != '\.':
                data_lines.append(lines[i])
                i += 1
            if i < len(lines):
                data_lines.append(lines[i])  # Add the \. line
                i += 1
            out_lines.extend([l + '\n' for l in clean_copy_block(table, dump_cols, schema_cols, data_lines)])
        else:
            i += 1
    with open(OUTPUT_FILE, 'w') as f:
        f.writelines(out_lines)
    print(f"LLM tables extracted and cleaned to {OUTPUT_FILE}")

if __name__ == '__main__':
    main() 