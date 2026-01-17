"""
Weekly Content Image Renderer
Generates square 1080×1080 images using ImageMagick with typography layout
"""

import subprocess
import os
import logging
from typing import Dict
from config.weekly_content_image_config import (
    CANVAS_SIZE, BG_COLOR, TEXT_COLOR, HEADER_FOOTER_COLOR,
    HEADER_FONT, BODY_FONT, ACCENT_FONT,
    LOGO_PATH, LOGO_CORNER, LOGO_SCALE, LOGO_PADDING,
    TOP_MARGIN, BOTTOM_MARGIN, SAFE_MARGIN,
    PHRASE_MAX_WIDTH, LINE_SPACING, TEXTURE_STRENGTH
)

logger = logging.getLogger(__name__)


def _build_imagemagick_command(
    category: str,
    title: str,
    scots_text: str,
    translation: str,
    series_footer: str,
    logo_path: str,
    output_path: str
) -> list:
    """
    Build complete ImageMagick command for square image generation.
    
    Returns list of command arguments for subprocess.
    """
    # ImageMagick v7 uses 'magick' command, v6 uses 'convert'
    # For v7, use 'magick' directly (not 'magick convert')
    import shutil
    if shutil.which('magick'):
        cmd = ['magick']
    else:
        cmd = ['convert']
    
    # Step 1: Create base canvas
    cmd.extend([
        '-size', f'{CANVAS_SIZE}x{CANVAS_SIZE}',
        f'xc:{BG_COLOR}'
    ])
    
    # Step 2: Header block (top) - pale blue to recede
    cmd.extend([
        '-gravity', 'north',
        '-pointsize', '48',
        '-font', HEADER_FONT,
        '-fill', HEADER_FOOTER_COLOR,
        '-annotate', f'+0+{TOP_MARGIN}', title
    ])
    
    # Step 3: Main Scots phrase (centered, larger) - increased size
    phrase_y_offset = -100
    cmd.extend([
        '-gravity', 'center',
        '-pointsize', '96',  # Increased from 72 to 96
        '-font', BODY_FONT,
        '-fill', TEXT_COLOR,
        '-annotate', f'+0{phrase_y_offset:+d}', scots_text
    ])
    
    # Step 4: Translation line (below phrase) - increased size
    translation_y_offset = 60  # Slightly more spacing
    translation_text = f'→ {translation}'
    cmd.extend([
        '-gravity', 'center',
        '-pointsize', '40',  # Increased from 32 to 40
        '-font', ACCENT_FONT,
        '-fill', TEXT_COLOR,
        '-annotate', f'+0+{translation_y_offset}', translation_text
    ])
    
    # Step 5: Footer (bottom) - pale blue to recede
    # Use -annotate with gravity south and positive offset from bottom
    # +0+{BOTTOM_MARGIN} places text BOTTOM_MARGIN pixels up from bottom edge
    cmd.extend([
        '-gravity', 'south',
        '-pointsize', '24',
        '-fill', HEADER_FOOTER_COLOR,
        '-annotate', f'+0+{BOTTOM_MARGIN}', series_footer
    ])
    
    # Step 6: Logo (corner placement) - only if logo_path provided
    if logo_path and os.path.exists(logo_path):
        # Convert corner name to ImageMagick gravity
        gravity_map = {
            'top-left': 'northwest',
            'top-right': 'northeast',
            'bottom-left': 'southwest',
            'bottom-right': 'southeast'
        }
        logo_gravity = gravity_map.get(LOGO_CORNER, 'southeast')
        
        # Calculate logo size
        logo_size = int(CANVAS_SIZE * LOGO_SCALE)
        
        # For ImageMagick composite, we'll do it in a separate step
        # Store logo composite info to do after base image is created
        # For now, skip logo in main command and composite separately
        pass  # Logo will be composited separately after base image
    else:
        logger.info("Skipping logo composite (logo file not found)")
    
    # Step 7: Export
    cmd.append(output_path)
    
    return cmd


def render_weekly_content_image(
    category: str,
    title: str,
    scots_text: str,
    translation: str,
    series_footer: str,
    logo_path: str = None,
    output_path: str = None
) -> Dict:
    """
    Render square 1080×1080 image using ImageMagick.
    
    Parameters
    ----------
    category:
        Content category ('weekly_word', 'weekly_phrase', or 'weekly_insult').
    title:
        Header title (e.g., 'SCOTS WORD OF THE WEEK').
    scots_text:
        The Scots text/phrase/word to display prominently.
    translation:
        English translation.
    series_footer:
        Footer text (e.g., 'Scots Language Series').
    logo_path:
        Absolute path to logo file.
    output_path:
        Absolute path where image should be saved.
    
    Returns
    -------
    Dict with:
    {
        'success': True/False,
        'output_path': '/path/to/image.png',
        'error': None or error message
    }
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Verify logo exists (if provided)
        if logo_path and not os.path.exists(logo_path):
            logger.warning(f"Logo file not found at {logo_path}, image will be generated without logo")
            logo_path = None
        
        # Build ImageMagick command
        cmd = _build_imagemagick_command(
            category=category,
            title=title,
            scots_text=scots_text,
            translation=translation,
            series_footer=series_footer,
            logo_path=logo_path,
            output_path=output_path
        )
        
        logger.info(f"Executing ImageMagick command: {' '.join(cmd)}")
        
        # Execute ImageMagick command to create base image
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Verify output file was created
        if not os.path.exists(output_path):
            return {
                'success': False,
                'output_path': None,
                'error': f"ImageMagick completed but output file not found at {output_path}"
            }
        
        # Step 7: Add footer text again after logo (ensure it's on top)
        # Re-add footer to ensure it's visible even after logo composite
        if logo_path and os.path.exists(logo_path):
            import shutil
            magick_cmd = 'magick' if shutil.which('magick') else 'convert'
            
            # Add footer text after logo composite (pale blue to recede)
            footer_cmd = [
                magick_cmd,
                output_path,
                '-gravity', 'south',
                '-pointsize', '24',
                '-fill', HEADER_FOOTER_COLOR,
                '-annotate', f'+0+{BOTTOM_MARGIN}', series_footer,
                output_path
            ]
            try:
                subprocess.run(footer_cmd, capture_output=True, text=True, check=True)
                logger.info("Footer text added after logo composite")
            except Exception as e:
                logger.warning(f"Could not re-add footer: {e}")
        
        # Step 8: Composite logo if provided (separate command for reliability)
        if logo_path and os.path.exists(logo_path):
            try:
                gravity_map = {
                    'top-left': 'northwest',
                    'top-right': 'northeast',
                    'bottom-left': 'southwest',
                    'bottom-right': 'southeast'
                }
                logo_gravity = gravity_map.get(LOGO_CORNER, 'southeast')
                logo_size = int(CANVAS_SIZE * LOGO_SCALE)
                
                # Composite logo using separate command
                # Syntax: magick base.png (logo.png -resize WxH) -gravity POS -geometry +X+Y -composite output.png
                import shutil
                magick_cmd = 'magick' if shutil.which('magick') else 'convert'
                
                # Use parentheses for grouping in ImageMagick
                # For subprocess, we need to escape or use a different approach
                # Create temp resized logo first, then composite
                import tempfile
                temp_logo = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_logo_path = temp_logo.name
                temp_logo.close()
                
                # First, resize the logo
                resize_cmd = [
                    magick_cmd,
                    logo_path,
                    '-resize', f'{logo_size}x{logo_size}',
                    temp_logo_path
                ]
                subprocess.run(resize_cmd, capture_output=True, check=True)
                
                # Then composite it onto the base image
                composite_cmd = [
                    magick_cmd,
                    output_path,
                    temp_logo_path,
                    '-gravity', logo_gravity,
                    '-geometry', f'+{LOGO_PADDING}+{LOGO_PADDING}',
                    '-composite',
                    output_path
                ]
                
                subprocess.run(
                    composite_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Clean up temp file
                try:
                    os.unlink(temp_logo_path)
                except:
                    pass
                
                logger.info("Logo composited successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Logo composite failed (continuing without logo): {e.stderr}")
            except Exception as e:
                logger.warning(f"Logo composite error (continuing without logo): {e}")
        
        # Verify file size is reasonable (at least 1KB)
        file_size = os.path.getsize(output_path)
        if file_size < 1024:
            return {
                'success': False,
                'output_path': output_path,
                'error': f"Output file too small ({file_size} bytes), may be corrupted"
            }
        
        logger.info(f"Successfully generated image at {output_path} ({file_size} bytes)")
        
        return {
            'success': True,
            'output_path': output_path,
            'error': None
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"ImageMagick error: {e.stderr or e.stdout or str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'output_path': None,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'output_path': None,
            'error': error_msg
        }
