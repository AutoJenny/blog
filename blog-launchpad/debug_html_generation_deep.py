#!/usr/bin/env python3
"""
Deep debug script to trace HTML generation step by step
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clan_publisher import ClanPublisher
from app import get_post_with_development, get_post_sections_with_images

def debug_html_generation_deep():
    print("=== DEEP HTML GENERATION DEBUG ===")
    
    # Get post and sections
    post = get_post_with_development(53)
    sections = get_post_sections_with_images(53)
    
    if not post or not sections:
        print("❌ Failed to get post data")
        return
    
    print(f"✅ Found post: {post.get('title', 'No title')}")
    print(f"✅ Found {len(sections)} sections")
    
    # Process images first
    publisher = ClanPublisher()
    print("\n=== STEP 1: Processing Images ===")
    uploaded_images = publisher.process_images(post, sections)
    print(f"✅ Images processed: {len(uploaded_images)} uploaded")
    
    # Now let's manually trace the HTML generation
    print("\n=== STEP 2: Manual HTML Generation Trace ===")
    
    html_parts = []
    
    # Header
    print("Adding header...")
    title = post.get('title') or post.get('main_title') or post.get('provisional_title') or 'Untitled Post'
    subtitle = post.get('subtitle', '')
    
    html_parts.append('<div class="mpblog-post">')
    html_parts.append('<header class="blog-post-header">')
    html_parts.append(f'<h1>{title}</h1>')
    
    if subtitle:
        html_parts.append(f'<div class="blog-post__subtitle">{subtitle}</div>')
    
    # Meta information
    created_at = post.get('created_at')
    try:
        if hasattr(created_at, 'strftime'):
            date_str = created_at.strftime('%B %d, %Y')
        elif isinstance(created_at, str):
            date_str = created_at
        else:
            date_str = str(created_at) if created_at else 'Unknown date'
    except Exception as e:
        print(f"⚠️ Date formatting failed: {e}")
        date_str = 'Unknown date'
    
    html_parts.append('<div class="post-meta">')
    html_parts.append('<span class="post-meta__author">By Caitrin Stewart</span>')
    html_parts.append('<span class="post-meta__separator"> | </span>')
    html_parts.append(f'<span class="post-meta__date">{date_str}</span>')
    html_parts.append('<span class="post-meta__separator"> | </span>')
    html_parts.append('<span class="post-meta__reading-time">6 min read</span>')
    html_parts.append('</div>')
    html_parts.append('</header>')
    
    # Header image
    print("Adding header image...")
    from app import find_header_image
    header_path = find_header_image(post['id'])
    if header_path and uploaded_images and header_path in uploaded_images:
        clan_url = uploaded_images[header_path]
        if clan_url:
            html_parts.append('<figure class="blog-post-image">')
            html_parts.append(f'<a title="Header image" href="{clan_url}" rel="lightbox[mpblog_{post.get("id", "unknown")}]" target="_blank">')
            html_parts.append(f'<img src="{clan_url}" alt="Header image" width="1200" height="800">')
            html_parts.append('</a>')
            caption = "Header image for " + post.get('title', 'this post')
            html_parts.append(f'<figcaption>{caption}</figcaption>')
            html_parts.append('</figure>')
    
    # Summary
    if post.get('summary'):
        html_parts.append('<div class="blog-post__summary">')
        html_parts.append(f'<p>{post["summary"]}</p>')
        html_parts.append('</div>')
    
    # Sections - THE CRITICAL PART
    print("\n=== STEP 3: Processing Sections ===")
    if sections:
        html_parts.append('<div class="blog-sections">')
        
        for i, section in enumerate(sections, 1):
            print(f"\n--- Processing Section {i} ---")
            
            # Section heading
            heading = section.get('section_heading') or 'Untitled Section'
            print(f"  Heading: {heading}")
            html_parts.append(f'<section class="blog-section" id="section-{i}">')
            html_parts.append(f'<h2>{heading}</h2>')
            
            # Section content
            print(f"  Getting content...")
            content = section.get('polished') or section.get('draft') or section.get('content') or 'No content available for this section.'
            print(f"  Content type: {type(content)}")
            print(f"  Content length: {len(content) if content else 0}")
            print(f"  Content preview: {content[:100] if content else 'None'}...")
            
            if content:
                html_parts.append('<div class="section-text">')
                
                # Test safe_html function manually
                print(f"  Testing safe_html...")
                try:
                    # Import the safe_html function logic
                    import re
                    import html
                    
                    text_str = str(content)
                    print(f"    Original length: {len(text_str)}")
                    
                    # Remove DOCTYPE, html, head, body tags
                    text_str = re.sub(r'<!DOCTYPE[^>]*>', '', text_str)
                    text_str = re.sub(r'<html[^>]*>', '', text_str)
                    text_str = re.sub(r'</html>', '', text_str)
                    text_str = re.sub(r'<head[^>]*>.*?</head>', '', text_str, flags=re.DOTALL)
                    text_str = re.sub(r'<body[^>]*>', '', text_str)
                    text_str = re.sub(r'</body>', '', text_str)
                    
                    # Fix double <p> tags
                    text_str = re.sub(r'<p>\s*<p>', '<p>', text_str)
                    text_str = re.sub(r'</p>\s*</p>', '</p>', text_str)
                    
                    # Clean up any remaining HTML entities that shouldn't be there
                    text_str = re.sub(r'&lt;', '<', text_str)
                    text_str = re.sub(r'&gt;', '>', text_str)
                    
                    cleaned_content = text_str
                    print(f"    Cleaned length: {len(cleaned_content)}")
                    print(f"    Cleaned preview: {cleaned_content[:100]}...")
                    
                    # Add to HTML
                    if cleaned_content.startswith('<p>') and cleaned_content.endswith('</p>'):
                        html_parts.append(cleaned_content)
                        print(f"    ✅ Added as-is (already wrapped)")
                    elif cleaned_content.startswith('<p>') or cleaned_content.endswith('</p>'):
                        html_parts.append(cleaned_content)
                        print(f"    ✅ Added as-is (partial HTML)")
                    else:
                        html_parts.append(f'<p>{cleaned_content}</p>')
                        print(f"    ✅ Wrapped in <p> tags")
                    
                except Exception as e:
                    print(f"    ❌ safe_html failed: {e}")
                    html_parts.append(f'<p>Error processing content: {str(e)}</p>')
                
                html_parts.append('</div>')
            else:
                print(f"  ❌ No content found")
                html_parts.append('<div class="section-text">')
                html_parts.append('<p>No content available for this section.</p>')
                html_parts.append('</div>')
            
            # Section image
            print(f"  Processing image...")
            if section.get('image') and section['image'].get('path') and not section['image'].get('placeholder'):
                img = section['image']
                print(f"    Image path: {img['path']}")
                
                # Test safe_url function manually
                try:
                    if uploaded_images and img['path'] in uploaded_images:
                        safe_path = uploaded_images[img['path']]
                        print(f"    ✅ Found in uploaded_images: {safe_path}")
                    else:
                        print(f"    ❌ Not found in uploaded_images")
                        safe_path = None
                    
                    if safe_path:
                        html_parts.append('<figure class="section-image">')
                        html_parts.append(f'<a title="{img.get("caption") or img.get("alt_text") or "Section image"}" href="{safe_path}" rel="lightbox[mpblog_{post.get("id", "unknown")}]" target="_blank">')
                        html_parts.append(f'<img alt="{img.get("alt_text", "Section image")}" src="{safe_path}"')
                        
                        if img.get('width'):
                            html_parts.append(f' width="{img["width"]}"')
                        if img.get('height'):
                            html_parts.append(f' height="{img["height"]}"')
                        
                        html_parts.append('>')
                        html_parts.append('</a>')
                        
                        if img.get('caption'):
                            html_parts.append(f'<figcaption>{img["caption"]}</figcaption>')
                            print(f"    ✅ Added caption: {img['caption']}")
                        
                        html_parts.append('</figure>')
                        print(f"    ✅ Image added successfully")
                    else:
                        print(f"    ❌ No safe path available")
                        
                except Exception as e:
                    print(f"    ❌ Image processing failed: {e}")
            else:
                print(f"    No image data")
            
            html_parts.append('</section>')
            print(f"  ✅ Section {i} completed")
            
            # Check current HTML length
            current_html = '\n'.join(html_parts)
            print(f"  Current HTML length: {len(current_html)}")
        
        html_parts.append('</div>')
        print(f"\n✅ All sections processed")
    
    # Footer
    if post.get('keywords'):
        html_parts.append('<footer class="article-footer">')
        html_parts.append('<div class="article-tags">')
        html_parts.append('<strong>Tags:</strong>')
        for keyword in post['keywords']:
            html_parts.append(f'<span class="tag">{keyword}</span>')
        html_parts.append('</div>')
        html_parts.append('</footer>')
    
    html_parts.append('</div>')
    
    # Final HTML
    final_html = '\n'.join(html_parts)
    print(f"\n=== FINAL RESULTS ===")
    print(f"Final HTML length: {len(final_html)}")
    print(f"Number of sections in HTML: {final_html.count('<h2>')}")
    print(f"Number of figcaptions in HTML: {final_html.count('<figcaption>')}")
    
    # Check for each section
    print(f"\n=== SECTION VERIFICATION ===")
    for i, section in enumerate(sections):
        heading = section.get('section_heading', f'Section {i+1}')
        if heading in final_html:
            print(f"✅ Section {i+1}: {heading} - FOUND")
        else:
            print(f"❌ Section {i+1}: {heading} - MISSING")
    
    # Save HTML for inspection
    with open('debug_generated_html.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"\n✅ HTML saved to debug_generated_html.html")
    
    return final_html

if __name__ == "__main__":
    debug_html_generation_deep()

