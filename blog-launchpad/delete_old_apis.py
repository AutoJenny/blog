#!/usr/bin/env python3
"""
Script to delete old redundant API endpoints from app.py
"""

import re

def delete_old_apis():
    # Read the file
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Define the old API patterns to remove
    old_apis = [
        # Blog post schedules
        r'@app\.route\(\'/api/syndication/facebook/schedules\', methods=\[\'GET\'\]\).*?def delete_blog_post_schedule\(schedule_id\):.*?return jsonify\(\{\'error\': str\(e\)\}\), 500\n',
        
        # Blog post queue
        r'@app\.route\(\'/api/syndication/facebook/queue\', methods=\[\'GET\'\]\).*?def clear_blog_post_queue\(\):.*?return jsonify\(\{\'error\': str\(e\)\}\), 500\n',
        
        # Daily product posts schedules  
        r'@app\.route\(\'/api/daily-product-posts/schedules\'\).*?def test_schedules\(\):.*?return jsonify\(\{\'error\': str\(e\)\}\), 500\n',
        
        # Daily product posts queue
        r'@app\.route\(\'/api/daily-product-posts/queue\', methods=\[\'GET\'\]\).*?def clear_queue\(\):.*?return jsonify\(\{\'error\': str\(e\)\}\), 500\n',
    ]
    
    # Remove each pattern
    for pattern in old_apis:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Write back to file
    with open('app.py', 'w') as f:
        f.write(content)
    
    print("Deleted old redundant API endpoints")

if __name__ == "__main__":
    delete_old_apis()
