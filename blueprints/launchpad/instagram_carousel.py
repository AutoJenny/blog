# blueprints/launchpad/instagram_carousel.py
"""Instagram carousel generation and posting functionality."""

from flask import Blueprint, jsonify, request, render_template
import logging
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime, timedelta, date, time
import pytz
from config.database import db_manager
from blueprints.llm_actions import LLMService
from blueprints.launchpad.instagram_carousel_api import post_instagram_carousel

bp = Blueprint('instagram_carousel', __name__)
logger = logging.getLogger(__name__)

def get_font(size=40, bold=False):
    """Get a font for text rendering."""
    try:
        # Try system fonts
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "Arial.ttf"
        ]
        
        for font_path in font_paths:
            try:
                if font_path.endswith('.ttc'):
                    # For .ttc files, use font index 0
                    font = ImageFont.truetype(font_path, size, index=0)
                else:
                    font = ImageFont.truetype(font_path, size)
                return font
            except:
                continue
        
        # Fallback to default font
        font = ImageFont.load_default()
        return font
    except:
        return None

def add_text_overlay(image, text, position='center', max_width=None, font_size=40, text_color=(255, 255, 255)):
    """
    Add text overlay to image with word wrapping and background for readability.
    
    Args:
        image: PIL Image object
        text: Text to overlay
        position: 'center', 'top', 'bottom'
        max_width: Maximum text width in pixels (default: 80% of image width)
        font_size: Font size
        text_color: Text color (R, G, B) tuple
    """
    if not text:
        return image
    
    try:
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(image)
        font = get_font(font_size)
        
        if max_width is None:
            max_width = int(image.width * 0.8)  # 80% of image width
        
        # Word wrap text
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            if font:
                word_bbox = draw.textbbox((0, 0), word, font=font)
                word_width = word_bbox[2] - word_bbox[0]
            else:
                word_width = len(word) * (font_size // 2)  # Approximate
            
            if current_width + word_width > max_width and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width + (word_width * 0.1)  # Add space width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total text height
        line_height = font_size * 1.3 if font else font_size * 1.2
        total_height = len(lines) * line_height
        
        # Calculate position
        padding = 40
        if position == 'center':
            y = (image.height - total_height) // 2
        elif position == 'top':
            y = padding
        else:  # bottom
            y = image.height - total_height - padding
        
        # Draw semi-transparent background for text
        bg_padding = 20
        bg_y = max(0, y - bg_padding)
        bg_height = min(image.height, total_height + (bg_padding * 2))
        
        # Create overlay with transparency
        overlay = Image.new('RGBA', (image.width, bg_height), (0, 0, 0, 180))  # Dark semi-transparent
        image.paste(overlay, (0, bg_y), overlay)
        
        # Draw text lines
        current_y = y
        for line in lines:
            if font:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (image.width - text_width) // 2  # Center horizontally
                
                # Draw text with shadow for better readability
                shadow_offset = 2
                draw.text((x + shadow_offset, current_y + shadow_offset), line, 
                         fill=(0, 0, 0, 200), font=font)
                draw.text((x, current_y), line, fill=text_color, font=font)
            else:
                x = (image.width - len(line) * (font_size // 2)) // 2
                draw.text((x, current_y), line, fill=text_color)
            
            current_y += line_height
        
    except Exception as e:
        logger.error(f"Error adding text overlay: {e}")
    
    return image

def truncate_text(text, max_words=50):
    """Truncate text to max_words, preserving sentences."""
    if not text:
        return ""
    
    words = text.split()
    if len(words) <= max_words:
        return text
    
    # Try to end at sentence boundary
    truncated = ' '.join(words[:max_words])
    
    # Find last sentence end
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    
    last_sentence = max(last_period, last_exclamation, last_question)
    
    if last_sentence > max_words * 0.7:  # If sentence end is reasonably close
        return truncated[:last_sentence + 1]
    
    return truncated + "..."

def create_carousel_slide(image_path, slide_number, slide_type, text=None, post_title=None):
    """
    Create a single carousel slide.
    
    Args:
        image_path: Path to portrait image (1080×1350px)
        slide_number: Slide number (1-10)
        slide_type: 'cover', 'section', 'summary', 'cta'
        text: Text overlay (optional)
        post_title: Post title for cover slide
    
    Returns:
        PIL Image object or None if error
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None
        
        # Load portrait image
        slide_image = Image.open(image_path)
        
        # Ensure correct dimensions
        if slide_image.size != (1080, 1350):
            slide_image = slide_image.resize((1080, 1350), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if slide_image.mode != 'RGB':
            rgb_image = Image.new('RGB', slide_image.size, (255, 255, 255))
            if slide_image.mode == 'RGBA':
                rgb_image.paste(slide_image, mask=slide_image.split()[3])
            else:
                rgb_image.paste(slide_image)
            slide_image = rgb_image
        
        # Add text overlay based on slide type
        if slide_type == 'cover' and post_title:
            # Cover slide: title at top, branding
            overlay_text = post_title
            slide_image = add_text_overlay(slide_image, overlay_text, position='top', 
                                          font_size=48, text_color=(255, 255, 255))
        
        elif slide_type == 'section' and text:
            # Section slide: 30-50 word summary, centered
            truncated_text = truncate_text(text, max_words=50)
            slide_image = add_text_overlay(slide_image, truncated_text, position='center',
                                          font_size=36, text_color=(255, 255, 255))
        
        elif slide_type == 'summary' and text:
            # Summary/quote slide
            truncated_text = truncate_text(text, max_words=60)
            slide_image = add_text_overlay(slide_image, truncated_text, position='center',
                                          font_size=38, text_color=(255, 255, 255))
        
        elif slide_type == 'cta':
            # CTA slide
            cta_text = "Read full story at clan.com/blog ✨\n(link in bio)"
            slide_image = add_text_overlay(slide_image, cta_text, position='center',
                                          font_size=44, text_color=(255, 255, 255))
        
        return slide_image
        
    except Exception as e:
        logger.error(f"Error creating carousel slide {slide_number}: {e}")
        import traceback
        traceback.print_exc()
        return None

def find_portrait_image(post_id, image_type='section', section_id=None):
    """
    Find portrait version of an image.
    Checks multiple possible locations: blog root, blog-images service, and generates on-the-fly if needed.
    """
    # List of possible paths to check
    possible_paths = []
    
    if image_type == 'header':
        possible_paths = [
            os.path.join('static', 'content', 'posts', str(post_id), 'header', 'portrait', 'header_portrait.jpg'),
            os.path.join('blog-images', 'static', 'content', 'posts', str(post_id), 'header', 'portrait', 'header_portrait.jpg'),
        ]
    elif image_type == 'section' and section_id:
        possible_paths = [
            os.path.join('static', 'content', 'posts', str(post_id), 'sections', str(section_id), 'portrait', f'section_{section_id}_portrait.jpg'),
            os.path.join('blog-images', 'static', 'content', 'posts', str(post_id), 'sections', str(section_id), 'portrait', f'section_{section_id}_portrait.jpg'),
        ]
    else:
        return None
    
    # Check each possible path
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If portrait doesn't exist, try to generate it on-the-fly from optimized image
    logger.info(f"Portrait not found, attempting to generate on-the-fly for {image_type} {section_id or 'header'}")
    return generate_portrait_on_the_fly(post_id, image_type, section_id)

def generate_portrait_on_the_fly(post_id, image_type='section', section_id=None):
    """
    Generate portrait image on-the-fly from optimized image if portrait doesn't exist.
    """
    try:
        # Find optimized image
        optimized_paths = []
        if image_type == 'header':
            optimized_paths = [
                os.path.join('static', 'content', 'posts', str(post_id), 'header', 'optimized'),
                os.path.join('blog-images', 'static', 'content', 'posts', str(post_id), 'header', 'optimized'),
            ]
        elif image_type == 'section' and section_id:
            optimized_paths = [
                os.path.join('static', 'content', 'posts', str(post_id), 'sections', str(section_id), 'optimized'),
                os.path.join('blog-images', 'static', 'content', 'posts', str(post_id), 'sections', str(section_id), 'optimized'),
            ]
        
        optimized_image_path = None
        for opt_dir in optimized_paths:
            if os.path.exists(opt_dir):
                # Get first image file
                for filename in os.listdir(opt_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        optimized_image_path = os.path.join(opt_dir, filename)
                        break
                if optimized_image_path:
                    break
        
        if not optimized_image_path or not os.path.exists(optimized_image_path):
            logger.warning(f"No optimized image found to generate portrait from for {image_type} {section_id or 'header'}")
            return None
        
        # Determine output path (save to blog-images directory to match API behavior)
        if image_type == 'header':
            output_dir = os.path.join('blog-images', 'static', 'content', 'posts', str(post_id), 'header', 'portrait')
            output_filename = 'header_portrait.jpg'
        else:
            output_dir = os.path.join('blog-images', 'static', 'content', 'posts', str(post_id), 'sections', str(section_id), 'portrait')
            output_filename = f'section_{section_id}_portrait.jpg'
        
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        
        # Import create_portrait_version from blog-images or define inline
        # For now, let's call the blog-images API to generate it
        try:
            response = requests.post(
                f'http://localhost:5005/api/portrait/generate/{post_id}/header' if image_type == 'header' 
                else f'http://localhost:5005/api/portrait/generate/{post_id}/section/{section_id}',
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Return the path where it was saved
                    return output_path
        except:
            pass
        
        # If API call fails, generate directly using PIL
        from PIL import Image
        
        # Use the portrait generation logic from blog-images
        result = create_portrait_version_direct(optimized_image_path, output_path)
        if result.get('success'):
            return output_path
        
        return None
        
    except Exception as e:
        logger.error(f"Error generating portrait on-the-fly: {e}")
        return None

def add_watermark_with_opacity_local(image, watermark, position='bottom-right', opacity=0.6):
    """Add watermark with specified opacity (0.0-1.0) for Instagram."""
    if watermark is None:
        return image
    
    from PIL import ImageEnhance
    
    # Resize watermark to reasonable size (max 200px width)
    watermark_width = min(200, image.width // 4)
    watermark_height = int(watermark.height * (watermark_width / watermark.width))
    watermark_resized = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
    
    # Create watermark with alpha channel for opacity control
    watermark_with_alpha = Image.new('RGBA', watermark_resized.size, (0, 0, 0, 0))
    watermark_with_alpha.paste(watermark_resized, (0, 0))
    
    # Apply opacity to alpha channel
    alpha = watermark_with_alpha.split()[3]
    alpha = alpha.point(lambda p: int(p * opacity))
    watermark_with_alpha.putalpha(alpha)
    
    # Calculate position with 10px margins
    margin = 10
    if position == 'bottom-right':
        x = image.width - watermark_width - margin
        y = image.height - watermark_height - margin
    else:
        x = margin
        y = image.height - watermark_height - margin
    
    # Create new image with alpha channel if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Paste watermark with opacity
    image.paste(watermark_with_alpha, (x, y), watermark_with_alpha)
    
    return image

def create_portrait_version_direct(source_image_path, output_path, target_width=1080, target_height=1350):
    """
    Direct version of create_portrait_version that can be called from carousel builder.
    """
    try:
        from PIL import Image
        
        # Load source image
        source_image = Image.open(source_image_path)
        
        # Convert to RGB if needed
        if source_image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', source_image.size, (255, 255, 255))
            if source_image.mode == 'P':
                source_image = source_image.convert('RGBA')
            rgb_image.paste(source_image, mask=source_image.split()[3] if source_image.mode == 'RGBA' else None)
            source_image = rgb_image
        elif source_image.mode != 'RGB':
            source_image = source_image.convert('RGB')
        
        # Calculate aspect ratios
        source_aspect = source_image.width / source_image.height
        target_aspect = target_width / target_height
        
        # Resize and crop/pad to fit target dimensions
        if source_aspect > target_aspect:
            new_height = int(target_width / source_aspect)
            resized = source_image.resize((target_width, new_height), Image.Resampling.LANCZOS)
            portrait_image = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            y_offset = (target_height - new_height) // 2
            portrait_image.paste(resized, (0, y_offset))
        else:
            new_width = int(target_height * source_aspect)
            resized = source_image.resize((new_width, target_height), Image.Resampling.LANCZOS)
            portrait_image = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            x_offset = (target_width - new_width) // 2
            portrait_image.paste(resized, (x_offset, 0))
        
        # Load and apply watermark if available
        watermark_paths = [
            os.path.join('static', 'images', 'site', 'clan-watermark.png'),
            os.path.join('blog-images', 'static', 'images', 'site', 'clan-watermark.png'),
        ]
        watermark = None
        for wm_path in watermark_paths:
            if os.path.exists(wm_path):
                try:
                    watermark = Image.open(wm_path)
                    break
                except:
                    pass
        
        if watermark:
            # Apply watermark with reduced opacity
            portrait_image = add_watermark_with_opacity_local(portrait_image, watermark, 'bottom-right', opacity=0.6)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert back to RGB if needed
        if portrait_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', portrait_image.size, (255, 255, 255))
            rgb_image.paste(portrait_image, mask=portrait_image.split()[3] if len(portrait_image.split()) == 4 else None)
            portrait_image = rgb_image
        
        # Save as JPG
        quality = 85
        portrait_image.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        # Check file size and reduce quality if needed
        file_size = os.path.getsize(output_path)
        max_size = 1024 * 1024  # 1MB
        
        if file_size > max_size:
            for q in range(80, 50, -5):
                portrait_image.save(output_path, 'JPEG', quality=q, optimize=True)
                if os.path.getsize(output_path) <= max_size:
                    break
        
        return {
            'success': True,
            'output_path': output_path,
            'file_size': os.path.getsize(output_path)
        }
        
    except Exception as e:
        logger.error(f"Error in create_portrait_version_direct: {e}")
        return {'success': False, 'error': str(e)}

def build_carousel_slides(post_id):
    """
    Build carousel slides from blog post.
    
    Returns:
        dict with success status and slide paths
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Get post data
            cursor.execute("""
                SELECT id, title, subtitle, summary, clan_uploaded_url
                FROM post
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return {
                    'success': False,
                    'error': 'Post not found'
                }
            
            # Get sections
            cursor.execute("""
                SELECT id, section_order, section_heading, section_description
                FROM post_section
                WHERE post_id = %s
                ORDER BY section_order
            """, (post_id,))
            sections = cursor.fetchall()
        
        # Create carousel directory
        carousel_dir = os.path.join('static', 'content', 'posts', str(post_id), 'instagram', 'carousel')
        os.makedirs(carousel_dir, exist_ok=True)
        
        slides = []
        missing_portraits = []
        
        # Slide 1: Cover with header image
        header_portrait = find_portrait_image(post_id, 'header')
        if header_portrait and os.path.exists(header_portrait):
            cover_slide = create_carousel_slide(
                header_portrait, 1, 'cover',
                post_title=post['title']
            )
            if cover_slide:
                cover_path = os.path.join(carousel_dir, '01_cover.jpg')
                cover_slide.save(cover_path, 'JPEG', quality=90, optimize=True)
                slides.append({
                    'slide_number': 1,
                    'type': 'cover',
                    'path': cover_path,
                    'url': f'/static/content/posts/{post_id}/instagram/carousel/01_cover.jpg'
                })
            else:
                missing_portraits.append('header')
        else:
            missing_portraits.append(f'header (expected at: {os.path.join("static", "content", "posts", str(post_id), "header", "portrait", "header_portrait.jpg")})')
        
        # Slides 2-8: Section slides (up to 7 sections)
        for idx, section in enumerate(sections[:7], start=2):
            section_portrait = find_portrait_image(post_id, 'section', section['id'])
            if section_portrait and os.path.exists(section_portrait):
                section_slide = create_carousel_slide(
                    section_portrait, idx, 'section',
                    text=section.get('section_description', section.get('section_heading', ''))
                )
                if section_slide:
                    slide_filename = f"{idx:02d}_section{section['section_order']}.jpg"
                    slide_path = os.path.join(carousel_dir, slide_filename)
                    section_slide.save(slide_path, 'JPEG', quality=90, optimize=True)
                    slides.append({
                        'slide_number': idx,
                        'type': 'section',
                        'section_id': section['id'],
                        'section_order': section['section_order'],
                        'path': slide_path,
                        'url': f'/static/content/posts/{post_id}/instagram/carousel/{slide_filename}'
                    })
                else:
                    missing_portraits.append(f'section {section["id"]}')
            else:
                expected_path = os.path.join('static', 'content', 'posts', str(post_id), 'sections', str(section['id']), 'portrait', f'section_{section["id"]}_portrait.jpg')
                missing_portraits.append(f'section {section["id"]} (expected at: {expected_path})')
        
        # Slide 9 (optional): Summary/quote slide
        if post.get('summary') and len(slides) < 9:
            # Use header image or first section image as background
            bg_image_path = header_portrait or (find_portrait_image(post_id, 'section', sections[0]['id']) if sections else None)
            
            if bg_image_path and os.path.exists(bg_image_path):
                summary_slide = create_carousel_slide(
                    bg_image_path, len(slides) + 1, 'summary',
                    text=post.get('summary', '')
                )
                if summary_slide:
                    slide_num = len(slides) + 1
                    slide_filename = f"{slide_num:02d}_summary.jpg"
                    slide_path = os.path.join(carousel_dir, slide_filename)
                    summary_slide.save(slide_path, 'JPEG', quality=90, optimize=True)
                    slides.append({
                        'slide_number': slide_num,
                        'type': 'summary',
                        'path': slide_path,
                        'url': f'/static/content/posts/{post_id}/instagram/carousel/{slide_filename}'
                    })
        
        # Slide 10: CTA slide
        cta_bg_path = header_portrait or (find_portrait_image(post_id, 'section', sections[0]['id']) if sections else None)
        if cta_bg_path and os.path.exists(cta_bg_path):
            cta_slide = create_carousel_slide(cta_bg_path, len(slides) + 1, 'cta')
            if cta_slide:
                slide_num = len(slides) + 1
                slide_filename = f"{slide_num:02d}_cta.jpg"
                slide_path = os.path.join(carousel_dir, slide_filename)
                cta_slide.save(slide_path, 'JPEG', quality=90, optimize=True)
                slides.append({
                    'slide_number': slide_num,
                    'type': 'cta',
                    'path': slide_path,
                    'url': f'/static/content/posts/{post_id}/instagram/carousel/{slide_filename}'
                })
        
        if not slides:
            error_msg = 'No slides could be generated. Missing portrait images: ' + ', '.join(missing_portraits)
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'missing_portraits': missing_portraits,
                'hint': 'Ensure portrait images have been generated. Check that optimized images exist first.'
            }
        
        return {
            'success': True,
            'post_id': post_id,
            'slides': slides,
            'slide_count': len(slides),
            'carousel_directory': carousel_dir,
            'warnings': missing_portraits if missing_portraits else None
        }
        
    except Exception as e:
        logger.error(f"Error building carousel slides: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

def generate_instagram_caption(post_id, use_llm=True):
    """
    Generate Instagram-optimized caption for blog post carousel.
    
    Args:
        post_id: Post ID
        use_llm: Whether to use LLM for optimization (default True)
    
    Returns:
        dict with caption text
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, subtitle, summary, clan_uploaded_url
                FROM post
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return {
                    'success': False,
                    'error': 'Post not found'
                }
        
        # Base hashtags
        hashtags = [
            '#scotland', '#tartan', '#scottishheritage', '#clans',
            '#madeinscotland', '#highlands', '#scottishdesign',
            '#heritagecraft', '#clancom', '#scottishculture'
        ]
        hashtag_string = ' '.join(hashtags)
        
        # Create base caption structure
        hook_line = post['title'][:80]  # First 10-15 words typically
        if len(hook_line) > 80:
            hook_line = hook_line.rsplit(' ', 1)[0] + "..."  # Cut at word boundary
        
        summary = post.get('summary', post.get('subtitle', ''))[:300]  # 2-3 sentences
        cta = "Read the full article on our blog — link in bio 🔗"
        
        if use_llm:
            try:
                # Use LLM to optimize the caption
                llm_service = LLMService()
                
                prompt = f"""Create an engaging Instagram caption for a blog post carousel.

Blog Post Title: {post['title']}
Subtitle: {post.get('subtitle', '')}
Summary: {post.get('summary', '')}

Create an Instagram caption with:
1. A hook line (≤10 words) that captures attention
2. A short summary (2-3 sentences, engaging and concise)
3. A call-to-action: "Read the full article on our blog — link in bio 🔗"
4. These hashtags: {hashtag_string}

Keep the total caption under 2200 characters (Instagram limit).
Make it engaging, authentic, and optimized for Instagram's audience.
Format: Hook line on first line, then summary, then CTA, then hashtags."""
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are a social media expert specializing in Instagram content creation for heritage and cultural brands."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                response = llm_service.execute_llm_request(
                    provider='ollama',
                    model='mistral',
                    messages=messages
                )
                
                if response and 'content' in response:
                    generated_caption = response['content'].strip()
                    # Ensure hashtags are included
                    if hashtag_string not in generated_caption:
                        generated_caption += f"\n\n{hashtag_string}"
                    
                    return {
                        'success': True,
                        'caption': generated_caption,
                        'hook_line': hook_line,
                        'summary': summary,
                        'cta': cta,
                        'hashtags': hashtag_string
                    }
            except Exception as e:
                logger.warning(f"LLM caption generation failed, using template: {e}")
                # Fall back to template-based caption
        
        # Template-based caption (fallback or if use_llm=False)
        caption_parts = [
            hook_line,
            "",
            summary if summary else post.get('subtitle', ''),
            "",
            cta,
            "",
            hashtag_string
        ]
        
        caption = '\n'.join(filter(None, caption_parts))
        
        return {
            'success': True,
            'caption': caption,
            'hook_line': hook_line,
            'summary': summary,
            'cta': cta,
            'hashtags': hashtag_string
        }
        
    except Exception as e:
        logger.error(f"Error generating Instagram caption: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

# API Routes

@bp.route('/api/instagram/carousel/build/<int:post_id>', methods=['POST'])
def api_build_carousel(post_id):
    """API endpoint to build carousel slides."""
    try:
        result = build_carousel_slides(post_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in API build carousel: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/instagram/carousel/preview/<int:post_id>', methods=['GET'])
def api_get_carousel_preview(post_id):
    """Get preview of carousel slides (if already built)."""
    try:
        carousel_dir = os.path.join('static', 'content', 'posts', str(post_id), 'instagram', 'carousel')
        
        if not os.path.exists(carousel_dir):
            return jsonify({
                'success': False,
                'error': 'Carousel not yet generated'
            }), 404
        
        slides = []
        for filename in sorted(os.listdir(carousel_dir)):
            if filename.endswith('.jpg') and filename[0:2].isdigit():
                slide_number = int(filename[0:2])
                slides.append({
                    'slide_number': slide_number,
                    'filename': filename,
                    'url': f'/static/content/posts/{post_id}/instagram/carousel/{filename}'
                })
        
        slides.sort(key=lambda x: x['slide_number'])
        
        return jsonify({
            'success': True,
            'post_id': post_id,
            'slides': slides,
            'slide_count': len(slides)
        })
        
    except Exception as e:
        logger.error(f"Error getting carousel preview: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/instagram/caption/generate/<int:post_id>', methods=['POST'])
def api_generate_instagram_caption(post_id):
    """Generate Instagram caption for a blog post."""
    try:
        data = request.get_json() or {}
        use_llm = data.get('use_llm', True)
        
        result = generate_instagram_caption(post_id, use_llm=use_llm)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in API generate caption: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_next_blog_post_for_instagram():
    """
    Auto-select most recent published blog post that hasn't been posted to Instagram yet.
    
    Returns:
        dict with post_id and post data, or None if no post found
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Get most recent published post with clan_uploaded_url
            cursor.execute("""
                SELECT id, title, subtitle, summary, clan_uploaded_url, created_at, updated_at
                FROM post
                WHERE status = 'published'
                  AND clan_uploaded_url IS NOT NULL
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 10
            """)
            posts = cursor.fetchall()
            
            if not posts:
                return None
            
            # Check each post to see if it's already been posted to Instagram
            for post in posts:
                post_id = post['id']
                
                # Check if already posted to Instagram
                cursor.execute("""
                    SELECT id, status, platform_post_id
                    FROM posting_queue
                    WHERE post_id = %s
                      AND platform = 'instagram'
                      AND content_type = 'blog_post'
                      AND status IN ('published', 'ready')
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (post_id,))
                
                existing_queue = cursor.fetchone()
                
                # Skip if already posted or queued
                if existing_queue:
                    if existing_queue['status'] == 'published':
                        logger.info(f"Post {post_id} already published to Instagram, skipping")
                        continue
                    elif existing_queue['status'] == 'ready':
                        logger.info(f"Post {post_id} already queued for Instagram, skipping")
                        continue
                
                # Found an unposted post
                return {
                    'post_id': post_id,
                    'title': post['title'],
                    'subtitle': post.get('subtitle'),
                    'summary': post.get('summary'),
                    'clan_uploaded_url': post['clan_uploaded_url'],
                    'created_at': post['created_at'],
                    'updated_at': post['updated_at']
                }
            
            # All recent posts have been posted
            return None
            
    except Exception as e:
        logger.error(f"Error getting next blog post for Instagram: {e}", exc_info=True)
        return None

def calculate_next_monday_slot(time_window_start='12:00', time_window_end='18:00', timezone='Europe/London'):
    """
    Calculate next Monday at a time within 12:00-18:00 UK time window.
    
    Args:
        time_window_start: Start time in HH:MM format (default '12:00')
        time_window_end: End time in HH:MM format (default '18:00')
        timezone: Timezone string (default 'Europe/London')
    
    Returns:
        dict with scheduled_date, scheduled_time, scheduled_timestamp, timezone
    """
    try:
        # Parse time window
        start_hour, start_min = map(int, time_window_start.split(':'))
        end_hour, end_min = map(int, time_window_end.split(':'))
        
        # Use middle of window as default (14:00)
        default_hour = (start_hour + end_hour) // 2
        default_time = time(default_hour, 0)
        
        # Get UK timezone
        uk_tz = pytz.timezone(timezone)
        now_uk = datetime.now(uk_tz)
        
        # Calculate days until next Monday (0=Monday, 6=Sunday)
        days_until_monday = (7 - now_uk.weekday()) % 7
        if days_until_monday == 0:
            # Today is Monday - check if we're past the window
            if now_uk.time() >= default_time:
                # Already past default time today, use next Monday
                days_until_monday = 7
        
        # Calculate next Monday date
        next_monday = now_uk.date() + timedelta(days=days_until_monday)
        
        # Create datetime in UK timezone
        next_monday_dt = uk_tz.localize(datetime.combine(next_monday, default_time))
        
        # Convert to UTC for database storage
        next_monday_utc = next_monday_dt.astimezone(pytz.UTC)
        
        return {
            'scheduled_date': next_monday,
            'scheduled_time': default_time,
            'scheduled_timestamp': next_monday_utc.replace(tzinfo=None),  # Remove timezone for database
            'timezone': timezone,
            'schedule_name': 'Instagram Blog Carousel - Monday'
        }
        
    except Exception as e:
        logger.error(f"Error calculating next Monday slot: {e}", exc_info=True)
        # Fallback to next Monday at 14:00
        now = datetime.now()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = (now + timedelta(days=days_until_monday)).date()
        
        return {
            'scheduled_date': next_monday,
            'scheduled_time': time(14, 0),
            'scheduled_timestamp': datetime.combine(next_monday, time(14, 0)),
            'timezone': 'Europe/London',
            'schedule_name': 'Instagram Blog Carousel - Monday'
        }

@bp.route('/api/instagram/carousel/auto-generate', methods=['POST'])
def api_auto_generate_carousel():
    """
    Auto-generate Instagram carousel: select post, generate portraits, build carousel, create caption, schedule.
    
    Returns preview data for UI review.
    """
    try:
        # Step 1: Auto-select blog post
        post_data = get_next_blog_post_for_instagram()
        
        if not post_data:
            return jsonify({
                'success': False,
                'error': 'No unposted blog articles found. All recent posts have already been processed.'
            }), 404
        
        post_id = post_data['post_id']
        logger.info(f"Auto-selected post {post_id} for Instagram carousel: {post_data['title']}")
        
        # Step 2: Generate portrait images (call blog-images service)
        portrait_generation_success = False
        try:
            portrait_response = requests.post(
                f'http://localhost:5005/api/portrait/generate-all/{post_id}',
                timeout=300  # 5 minutes timeout for image processing
            )
            
            if portrait_response.status_code == 200:
                portrait_data = portrait_response.json()
                if portrait_data.get('success'):
                    success_count = portrait_data.get('results', {}).get('success_count', 0)
                    failed_count = portrait_data.get('results', {}).get('failed_count', 0)
                    logger.info(f"Generated {success_count} portrait images, {failed_count} failed")
                    if success_count > 0:
                        portrait_generation_success = True
                    else:
                        logger.warning("Portrait generation returned success but no images were generated")
                else:
                    logger.error(f"Portrait generation failed: {portrait_data.get('error')}")
            else:
                logger.error(f"Portrait generation returned {portrait_response.status_code}: {portrait_response.text}")
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'error': 'Cannot connect to blog-images service (port 5005). Please ensure the service is running.',
                'post_id': post_id
            }), 500
        except Exception as e:
            logger.error(f"Portrait generation error: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Failed to generate portrait images: {str(e)}',
                'post_id': post_id
            }), 500
        
        # Check if portraits exist before building carousel
        if not portrait_generation_success:
            # Verify portraits actually exist
            portrait_exists = False
            try:
                # Check if header portrait exists
                header_portrait = find_portrait_image(post_id, 'header')
                if header_portrait and os.path.exists(header_portrait):
                    portrait_exists = True
                else:
                    # Check if any section portraits exist
                    with db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT id FROM post_section WHERE post_id = %s LIMIT 1
                        """, (post_id,))
                        section = cursor.fetchone()
                        if section:
                            section_portrait = find_portrait_image(post_id, 'section', section['id'])
                            if section_portrait and os.path.exists(section_portrait):
                                portrait_exists = True
            except Exception as e:
                logger.warning(f"Error checking portrait existence: {e}")
            
            if not portrait_exists:
                return jsonify({
                    'success': False,
                    'error': 'Portrait images not found. Please ensure optimized images exist and portrait generation completed successfully.',
                    'post_id': post_id,
                    'hint': 'Try generating portraits manually first, or check that optimized images exist for this post'
                }), 500
        
        # Step 3: Build carousel slides
        carousel_result = build_carousel_slides(post_id)
        
        if not carousel_result['success']:
            return jsonify({
                'success': False,
                'error': f'Failed to build carousel: {carousel_result.get("error")}',
                'post_id': post_id
            }), 500
        
        # Step 4: Generate caption
        caption_result = generate_instagram_caption(post_id, use_llm=True)
        
        if not caption_result['success']:
            # Use fallback template caption
            logger.warning(f"LLM caption generation failed, using template")
            caption_result = generate_instagram_caption(post_id, use_llm=False)
        
        # Step 5: Calculate Monday schedule
        schedule = calculate_next_monday_slot()
        
        # Step 6: Create queue entry
        with db_manager.get_cursor() as cursor:
            # Check if carousel columns exist, otherwise use NULL
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'posting_queue' 
                    AND column_name IN ('carousel_slide_count', 'carousel_directory_path')
                """)
                existing_columns = [row['column_name'] for row in cursor.fetchall()]
                has_carousel_count = 'carousel_slide_count' in existing_columns
                has_carousel_dir = 'carousel_directory_path' in existing_columns
            except:
                has_carousel_count = False
                has_carousel_dir = False
            
            # Build INSERT statement dynamically based on available columns
            base_fields = [
                'post_id', 'content_type', 'platform', 'channel_type',
                'generated_content', 'post_title',
                'scheduled_date', 'scheduled_time', 'scheduled_timestamp',
                'schedule_name', 'timezone',
                'status'
            ]
            base_values = [
                post_id,
                'blog_post',
                'instagram',
                'carousel',
                caption_result.get('caption', ''),
                post_data['title'],
                schedule['scheduled_date'],
                schedule['scheduled_time'],
                schedule['scheduled_timestamp'],
                schedule['schedule_name'],
                schedule['timezone'],
                'ready'  # Status: ready for review
            ]
            
            if has_carousel_count:
                base_fields.append('carousel_slide_count')
                base_values.append(carousel_result.get('slide_count', 0))
            
            if has_carousel_dir:
                base_fields.append('carousel_directory_path')
                base_values.append(carousel_result.get('carousel_directory', ''))
            
            fields_str = ', '.join(base_fields)
            placeholders = ', '.join(['%s'] * len(base_values))
            
            cursor.execute(f"""
                INSERT INTO posting_queue ({fields_str}, created_at, updated_at)
                VALUES ({placeholders}, NOW(), NOW())
                RETURNING id
            """, tuple(base_values))
            
            queue_item = cursor.fetchone()
            queue_item_id = queue_item['id'] if queue_item else None
            
            conn = cursor.connection
            conn.commit()
        
        # Return preview data
        return jsonify({
            'success': True,
            'post_id': post_id,
            'post_title': post_data['title'],
            'queue_item_id': queue_item_id,
            'carousel': {
                'slide_count': carousel_result.get('slide_count', 0),
                'slides': carousel_result.get('slides', []),
                'directory': carousel_result.get('carousel_directory', '')
            },
            'caption': {
                'text': caption_result.get('caption', ''),
                'hook_line': caption_result.get('hook_line', ''),
                'summary': caption_result.get('summary', ''),
                'cta': caption_result.get('cta', ''),
                'hashtags': caption_result.get('hashtags', '')
            },
            'schedule': {
                'scheduled_date': schedule['scheduled_date'].isoformat() if isinstance(schedule['scheduled_date'], date) else str(schedule['scheduled_date']),
                'scheduled_time': str(schedule['scheduled_time']),
                'scheduled_timestamp': schedule['scheduled_timestamp'].isoformat() if isinstance(schedule['scheduled_timestamp'], datetime) else str(schedule['scheduled_timestamp']),
                'timezone': schedule['timezone'],
                'schedule_name': schedule['schedule_name']
            },
            'message': f'Carousel generated and queued for review. Scheduled for {schedule["scheduled_date"]} at {schedule["scheduled_time"]} {schedule["timezone"]}'
        })
        
    except Exception as e:
        logger.error(f"Error in auto-generate carousel: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/instagram/carousel/post/<int:post_id>', methods=['POST'])
def api_post_instagram_carousel(post_id):
    """API endpoint to post Instagram carousel."""
    try:
        data = request.get_json() or {}
        queue_item_id = data.get('queue_item_id')
        
        result = post_instagram_carousel(post_id, queue_item_id=queue_item_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in API post carousel: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/instagram/carousel/<int:post_id>/review')
def carousel_review(post_id):
    """Review interface for Instagram carousel."""
    return render_template('launchpad/instagram/carousel_review.html', post_id=post_id)

@bp.route('/api/instagram/carousel/queue', methods=['GET'])
def api_get_carousel_queue():
    """Get Instagram carousel queue items."""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, post_id, post_title, generated_content, 
                       scheduled_date, scheduled_time, scheduled_timestamp,
                       schedule_name, timezone, status, created_at, updated_at
                FROM posting_queue
                WHERE platform = 'instagram' 
                  AND channel_type = 'carousel'
                  AND content_type = 'blog_post'
                ORDER BY scheduled_timestamp ASC NULLS LAST, created_at DESC
            """)
            items = cursor.fetchall()
            
            items_list = []
            for item in items:
                items_list.append({
                    'id': item['id'],
                    'post_id': item['post_id'],
                    'post_title': item['post_title'],
                    'caption': item['generated_content'],
                    'scheduled_date': item['scheduled_date'].isoformat() if item['scheduled_date'] else None,
                    'scheduled_time': str(item['scheduled_time']) if item['scheduled_time'] else None,
                    'scheduled_timestamp': item['scheduled_timestamp'].isoformat() if item['scheduled_timestamp'] else None,
                    'schedule_name': item['schedule_name'],
                    'timezone': item['timezone'],
                    'status': item['status'],
                    'created_at': item['created_at'].isoformat() if item['created_at'] else None,
                    'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None
                })
            
            return jsonify({
                'success': True,
                'items': items_list,
                'count': len(items_list)
            })
    except Exception as e:
        logger.error(f"Error getting carousel queue: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
