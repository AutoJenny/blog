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
    USAGE_COLOR, PROVENANCE_COLOR,
    HEADER_FONT, BODY_FONT, ACCENT_FONT,
    LOGO_PATH, LOGO_CORNER, LOGO_SCALE, LOGO_PADDING,
    TOP_MARGIN, BOTTOM_MARGIN, SAFE_MARGIN,
    PHRASE_MAX_WIDTH, LINE_SPACING, TEXTURE_STRENGTH,
    USAGE_SPACING, USAGE_LINE_SPACING, PROVENANCE_SPACING, PROVENANCE_FONT_SIZE
)

logger = logging.getLogger(__name__)


def _build_imagemagick_command(
    category: str,
    title: str,
    scots_text: str,
    translation: str,
    series_footer: str,
    logo_path: str,
    output_path: str,
    usage_examples: list = None,
    notes: str = None
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
    
    # Step 3: Main Scots phrase (centered, larger)
    # Adjust vertical position based on whether we have usage examples (words need more space below)
    if usage_examples and len(usage_examples) > 0:
        # For words with usage examples, position slightly higher to accommodate extra content
        phrase_y_offset = -120
    else:
        # For phrases/insults, keep original position
        phrase_y_offset = -100
    
    # Use label: for automatic text wrapping (ImageMagick handles wrapping at word boundaries)
    # This ensures long phrases/insults wrap properly instead of being cut off
    # label: automatically wraps text within the specified width
    phrase_pointsize = 96  # Default size
    
    # For very long text, we'll reduce font size to ensure it fits nicely
    # Rough estimate: 96pt font ≈ 6 pixels per character
    estimated_width = len(scots_text) * 6
    if estimated_width > PHRASE_MAX_WIDTH:
        # Calculate how many lines we'll need
        chars_per_line = PHRASE_MAX_WIDTH / 6
        estimated_lines = max(2, (len(scots_text) / chars_per_line))
        # Reduce font size if more than 2 lines, but not below 72pt
        if estimated_lines > 2:
            phrase_pointsize = max(72, int(96 * (2 / estimated_lines)))
    
    # Use label: operation which supports automatic wrapping
    # Create label with transparent background that will be composited
    # Note: We'll handle this in a separate step after base canvas creation
    # Store the text rendering info - we'll composite it properly in render function
    # For now, skip main text in base command - will add with wrapping
    pass  # Main text will be added with wrapping in render function
    
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
    
    # Step 4.5: Usage examples (if provided - for weekly_word only)
    # Positioned below translation, in cream italics with quotation marks
    if usage_examples and len(usage_examples) > 0:
        current_y = translation_y_offset + USAGE_SPACING
        for i, usage in enumerate(usage_examples):
            if usage.strip():
                # Format with quotation marks and italic styling for visual distinction
                # Use a serif italic font for more elegant example styling
                # Add subtle leading/trailing spacing in quotes for visual breathing room
                usage_text = f'"{usage.strip()}"'
                cmd.extend([
                    '-gravity', 'center',
                    '-pointsize', '40',  # Same size as translation
                    '-font', 'Baskerville-Italic',  # Serif italic for elegant examples
                    '-fill', USAGE_COLOR,  # Cream color (slightly muted from main text)
                    '-annotate', f'+0+{current_y}', usage_text
                ])
                current_y += USAGE_LINE_SPACING
    
    # Step 4.6: Provenance/Notes (if provided)
    # Positioned below usage examples (or translation if no usage), in grey
    # Subtle metadata styling to recede into background
    if notes and notes.strip():
        # Calculate Y offset based on whether usage examples exist
        if usage_examples and len(usage_examples) > 0:
            # Start after all usage examples
            provenance_y = translation_y_offset + USAGE_SPACING + (len(usage_examples) * USAGE_LINE_SPACING) + PROVENANCE_SPACING
        else:
            # Start after translation
            provenance_y = translation_y_offset + PROVENANCE_SPACING
        
        # Format provenance with subtle styling (smaller, grey, clean sans)
        provenance_text = notes.strip()
        cmd.extend([
            '-gravity', 'center',
            '-pointsize', str(PROVENANCE_FONT_SIZE),  # Slightly smaller for hierarchy
            '-font', ACCENT_FONT,  # Clean sans for metadata
            '-fill', PROVENANCE_COLOR,  # Medium grey (subtle, recedes)
            '-annotate', f'+0+{provenance_y}', provenance_text
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
    output_path: str = None,
    usage_examples: list = None,
    notes: str = None
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
            output_path=output_path,
            usage_examples=usage_examples or [],
            notes=notes
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
        
        # Step 6.5: Add main Scots text with proper wrapping
        # Use label: for automatic text wrapping to prevent text from being cut off
        import shutil
        import tempfile
        magick_cmd = 'magick' if shutil.which('magick') else 'convert'
        
        # Always use label: for main Scots text to ensure proper wrapping
        # -annotate doesn't respect boundaries and can truncate text
        # label: automatically wraps at word boundaries within the specified width
        estimated_width = len(scots_text) * 12  # More accurate pixels per character at 96pt italic
        
        # Adjust vertical position
        if usage_examples and len(usage_examples) > 0:
            phrase_y_offset = -120
        else:
            phrase_y_offset = -100
        
        # Always use wrapping for main text to prevent truncation
        try:
            # Calculate optimal font size for wrapping
                # Use 12px per character for 96pt font (more accurate for italic serif)
                chars_per_line = PHRASE_MAX_WIDTH / 12  # More accurate estimate
                estimated_lines = max(2, (len(scots_text) / chars_per_line))
                if estimated_lines > 2:
                    phrase_pointsize = max(72, int(96 * (2 / estimated_lines)))
                else:
                    phrase_pointsize = 96
                
                # Create wrapped text label with transparent background
                temp_label = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_label_path = temp_label.name
                temp_label.close()
                
                # Create label with automatic wrapping (ImageMagick wraps at word boundaries)
                # Escape quotes in text for shell safety
                escaped_text = scots_text.replace('"', '\\"').replace("'", "\\'")
                label_cmd = [
                    magick_cmd,
                    '-background', 'transparent',
                    '-size', f'{PHRASE_MAX_WIDTH}x',  # Width constraint for wrapping
                    '-gravity', 'center',
                    '-pointsize', str(phrase_pointsize),
                    '-font', BODY_FONT,
                    '-fill', TEXT_COLOR,
                    f'label:{escaped_text}',
                    temp_label_path
                ]
                result = subprocess.run(label_cmd, capture_output=True, text=True, check=True)
                logger.debug(f"Label command output: {result.stdout}")
                if result.stderr:
                    logger.debug(f"Label command stderr: {result.stderr}")
                
                # Composite the wrapped text label onto the base image
                composite_cmd = [
                    magick_cmd,
                    output_path,
                    temp_label_path,
                    '-gravity', 'center',
                    '-geometry', f'+0{phrase_y_offset:+d}',
                    '-composite',
                    output_path
                ]
                result2 = subprocess.run(composite_cmd, capture_output=True, text=True, check=True)
                logger.debug(f"Composite command output: {result2.stdout}")
                if result2.stderr:
                    logger.debug(f"Composite command stderr: {result2.stderr}")
                
                # Clean up temp file
                try:
                    os.unlink(temp_label_path)
                except:
                    pass
                
                logger.info(f"Applied text wrapping ({len(scots_text)} chars, {phrase_pointsize}pt)")
        except Exception as e:
            logger.error(f"Text wrapping failed: {e}")
            # If wrapping fails, we still need to add the text somehow
            # Use annotate as last resort, but log the error
            try:
                add_text_cmd = [
                    magick_cmd,
                    output_path,
                    '-gravity', 'center',
                    '-pointsize', '96',
                    '-font', BODY_FONT,
                    '-fill', TEXT_COLOR,
                    '-annotate', f'+0{phrase_y_offset:+d}', scots_text,
                    output_path
                ]
                subprocess.run(add_text_cmd, capture_output=True, text=True, check=True)
                logger.warning("Used fallback annotate method (text may be truncated)")
            except Exception as e2:
                logger.error(f"Failed to add text even with fallback: {e2}")
        
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
