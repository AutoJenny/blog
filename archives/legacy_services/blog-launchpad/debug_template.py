#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
import os

# Create a simple test environment
env = Environment(loader=FileSystemLoader('templates'))

# Add the strip_html_doc filter
def strip_html_doc(content):
    """Strip HTML document structure and return only body content."""
    if not content:
        return content
    
    # Remove DOCTYPE declaration
    import re
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove html, head, and body tags, keeping only the content inside body
    content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Remove any remaining malformed HTML closing tags
    content = re.sub(r'</html[^>]*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</body[^>]*', '', content, flags=re.IGNORECASE)
    
    # Clean up any remaining whitespace and newlines
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'>\s+<', '><', content)
    
    return content.strip()

# Add a custom filter for clan.com widgets
def clan_widget(widget_type, id_value, title):
    """Generate clan.com widget syntax without HTML escaping."""
    if widget_type == 'product':
        return f'{{{{widget type="swcatalog/widget_crossSell_product" product_id="{id_value}" title="{title}"}}}}'
    elif widget_type == 'category':
        return f'{{{{widget type="swcatalog/widget_crossSell_category" category_id="{id_value}" title="{title}"}}}}'
    return ''

env.filters['strip_html_doc'] = strip_html_doc
env.filters['clan_widget'] = clan_widget

# Test data
post = {
    'id': 53, 
    'title': 'Test Post', 
    'cross_promotion': {
        'product_id': '62208', 
        'category_id': '98'
    }
}

sections = [
    {
        'id': 1, 
        'section_heading': 'Test Section 1', 
        'polished': '<p>This is <strong>polished</strong> content for section 1</p>', 
        'draft': '<p>This is draft content for section 1</p>', 
        'content': '<p>This is content for section 1</p>'
    },
    {
        'id': 2, 
        'section_heading': 'Test Section 2', 
        'polished': '<p>This is <strong>polished</strong> content for section 2</p>', 
        'draft': '<p>This is draft content for section 2</p>', 
        'content': '<p>This is content for section 2</p>'
    }
]

# Load and render template
template = env.get_template('clan_post.html')
print("Rendering template...")
html = template.render(post=post, sections=sections)

print(f"\nHTML LENGTH: {len(html)}")
print("\nHTML PREVIEW (first 1000 chars):")
print(html[:1000])
print("\nHTML PREVIEW (last 1000 chars):")
print(html[-1000:])

# Check if sections are being rendered
if 'Test Section 1' in html:
    print("\n✅ Section headings found")
else:
    print("\n❌ Section headings NOT found")

if 'polished content for section 1' in html:
    print("✅ Section content found")
else:
    print("❌ Section content NOT found")

# Look for specific patterns
print("\n--- DEBUGGING ---")
print("Looking for section content...")
for i, section in enumerate(sections):
    print(f"Section {i+1}: {section['section_heading']}")
    if section['polished'] in html:
        print(f"  ✅ Polished content found: {section['polished'][:50]}...")
    else:
        print(f"  ❌ Polished content NOT found")
    
    if section['draft'] in html:
        print(f"  ✅ Draft content found: {section['draft'][:50]}...")
    else:
        print(f"  ❌ Draft content NOT found")
    
    if section['content'] in html:
        print(f"  ✅ Content found: {section['content'][:50]}...")
    else:
        print(f"  ❌ Content NOT found")

