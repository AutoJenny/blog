import re

INPUT_FILE = 'blog_data_only_20250528.sql'
OUTPUT_FILE = 'blog_data_only_20250528_transformed.sql'

# New schema columns for llm_action
NEW_COLUMNS = [
    'id', 'field_name', 'description', 'provider_id', 'llm_model', 'prompt_template_id',
    'temperature', 'max_tokens', 'order', 'created_at', 'updated_at', 'input_field', 'output_field'
]

# Old columns in the dump
OLD_COLUMNS = [
    'id', 'field_name', 'prompt_template', 'prompt_template_id', 'llm_model',
    'temperature', 'max_tokens', 'order', 'created_at', 'updated_at', 'input_field', 'output_field'
]

def transform_llm_action_block(lines):
    out = []
    for line in lines:
        if line.strip() == '\\.':
            out.append('\\.')
            break
        # Split by tab, old order
        parts = line.rstrip('\n').split('\t')
        if len(parts) != len(OLD_COLUMNS):
            out.append(line)
            continue
        # Map old to new: remove prompt_template, add description (empty), provider_id (1)
        new_parts = [
            parts[0],  # id
            parts[1],  # field_name
            '',        # description (empty)
            '1',       # provider_id (default 1)
            parts[4],  # llm_model
            parts[3],  # prompt_template_id
            parts[5],  # temperature
            parts[6],  # max_tokens
            parts[7],  # order
            parts[8],  # created_at
            parts[9],  # updated_at
            parts[10], # input_field
            parts[11], # output_field
        ]
        out.append('\t'.join(new_parts))
    return out

def main():
    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('COPY public.llm_action '):
            # Write new COPY header
            out_lines.append('COPY public.llm_action (' + ', '.join(NEW_COLUMNS) + ') FROM stdin;\n')
            i += 1
            # Transform block
            block_lines = []
            while i < len(lines) and lines[i].strip() != '\\.':
                block_lines.append(lines[i])
                i += 1
            if i < len(lines):
                block_lines.append(lines[i])  # Add the \. line
                i += 1
            out_lines.extend(transform_llm_action_block(block_lines))
        else:
            out_lines.append(line)
            i += 1
    with open(OUTPUT_FILE, 'w') as f:
        f.writelines(out_lines)
    print(f"Transformed dump written to {OUTPUT_FILE}")

if __name__ == '__main__':
    main() 