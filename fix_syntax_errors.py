#!/usr/bin/env python3
"""
Fix syntax errors in extracted modules
"""

import os
import re

def fix_file(file_path):
    """Fix syntax errors in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix common issues
    # 1. Fix unmatched parentheses in docstrings
    content = re.sub(r'\([^)]*$', '', content, flags=re.MULTILINE)
    
    # 2. Fix any remaining syntax issues
    lines = content.splitlines()
    fixed_lines = []
    
    for line in lines:
        # Skip lines with unmatched parentheses
        if '(' in line and ')' not in line and not line.strip().startswith('#'):
            # Try to fix by adding closing parenthesis
            if line.count('(') > line.count(')'):
                line = line + ')' * (line.count('(') - line.count(')'))
        fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(fixed_lines))

# Fix all Python files in app directory
for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            print(f"Fixing {file_path}...")
            fix_file(file_path)

print("Syntax fixes complete!")
