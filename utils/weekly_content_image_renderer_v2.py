"""
Weekly Content Image Renderer V2 - Corrected Approach
Generates square 1080×1080 images using ImageMagick with proper font sizing and wrapping

Key improvements:
- Fixed moderate font size (72pt) for all text
- Actual text dimension measurement using ImageMagick metrics
- Proper wrapping calculation based on rendered width
- Dynamic vertical layout based on actual text heights
- Better spacing between elements
"""

import subprocess
import os
import logging
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional
from config.weekly_content_image_config import (
    CANVAS_SIZE, BG_COLOR, TEXT_COLOR, HEADER_FOOTER_COLOR,
    USAGE_COLOR, PROVENANCE_COLOR,
    HEADER_FONT, BODY_FONT, ACCENT_FONT,
    LOGO_PATH, LOGO_CORNER, LOGO_SCALE, LOGO_PADDING,
    TOP_MARGIN, BOTTOM_MARGIN, SAFE_MARGIN,
    PHRASE_MAX_WIDTH
)

logger = logging.getLogger(__name__)

# Base font sizes (will be adjusted dynamically)
SCOTS_TEXT_FONT_SIZE_BASE = 72  # Base size for multi-line Scots text
SCOTS_WORD_FONT_SIZE_BASE = 56  # Base size for single words
TRANSLATION_FONT_SIZE_BASE = 40
USAGE_FONT_SIZE_BASE = 36
PROVENANCE_FONT_SIZE = 32
HEADER_FONT_SIZE = 48
FOOTER_FONT_SIZE = 24

# Base spacing (will be adjusted dynamically)
SCOTS_TO_TRANSLATION_SPACING_BASE = 120
TRANSLATION_TO_USAGE_SPACING = 70
USAGE_LINE_SPACING = 55
USAGE_TO_PROVENANCE_SPACING = 60
LINE_HEIGHT_MULTIPLIER = 1.3
DESCENDER_BUFFER = 40


def calculate_scots_font_size_by_height(category: str, scots_text: str, max_height: int) -> Tuple[int, int, List[str]]:
    """
    Calculate Scots font size to FILL 80-90% of budget, not just "shrink to fit".
    Returns: (font_size, actual_height, wrapped_lines)
    
    Rule: Try to fill 80-90% of max_height, only shrink if overflow occurs
    Hard caps: Maximum 56pt, Minimum 40pt (48pt for short content)
    """
    # Starting font sizes by category
    if category == 'weekly_word':
        start_size = 56
    elif category == 'weekly_phrase':
        start_size = 54
    else:  # weekly_insult
        start_size = 52
    
    max_font = 56
    min_font = 40
    
    # Target: fill 80-90% of max_height (not just "fit")
    target_height_min = int(max_height * 0.80)
    target_height_max = int(max_height * 0.90)
    
    # Try decreasing font sizes, looking for one that fills the target range
    best_font = None
    best_height = 0
    best_lines = []
    
    for font_size in range(start_size, min_font - 1, -2):  # Decrease by 2pt each step
        width, height, lines = _measure_text_dimensions(
            scots_text, BODY_FONT, font_size, PHRASE_MAX_WIDTH
        )
        
        # If it fits and fills target range, use it
        if target_height_min <= height <= target_height_max:
            return font_size, height, lines
        
        # If it fits but is too small, remember it as fallback
        if height <= max_height:
            if best_font is None or height > best_height:
                best_font = font_size
                best_height = height
                best_lines = lines
    
    # Use best fit if we found one
    if best_font is not None:
        return best_font, best_height, best_lines
    
    # Last resort: use minimum
    font_size = min_font
    width, height, lines = _measure_text_dimensions(
        scots_text, BODY_FONT, font_size, PHRASE_MAX_WIDTH
    )
    return font_size, height, lines


def calculate_translation_font_size(translation_text: str, max_height: int, max_width: int = 760) -> Tuple[int, int]:
    """
    Calculate translation font size (32-38pt range).
    Max height: 14% of canvas (≈150px)
    Translation should be clearly readable, not metadata-small.
    """
    for font_size in range(38, 31, -2):  # Try 38, 36, 34, 32
        width, height, _ = _measure_text_dimensions(
            translation_text, ACCENT_FONT, font_size, max_width
        )
        if height <= max_height:
            return font_size, height
    
    # Use minimum if still too tall
    font_size = 32
    width, height, _ = _measure_text_dimensions(
        translation_text, ACCENT_FONT, font_size, max_width
    )
    return font_size, height


def calculate_usage_font_size(usage_examples: List[str], max_height: int) -> Tuple[int, int]:
    """
    Calculate usage examples font size (28-34pt range).
    Max combined height: 22% of canvas
    Line height multiplier: 1.35
    Usage examples should feel nearly as important as translation, not secondary clutter.
    """
    if not usage_examples:
        return 0, 0
    
    USAGE_LINE_HEIGHT_MULTIPLIER = 1.35  # Increased from 1.3
    
    for font_size in range(34, 27, -2):  # Try 34, 32, 30, 28
        heights = []
        for usage in usage_examples:
            if usage.strip():
                usage_text = f'"{usage.strip()}"'
                _, h, _ = _measure_text_dimensions(
                    usage_text, 'Baskerville-Italic', font_size
                )
                # Apply line height multiplier
                h = int(h * USAGE_LINE_HEIGHT_MULTIPLIER)
                heights.append(h)
        
        # Spacing between usage examples
        usage_spacing = int(font_size * 0.8)  # Proportional spacing
        total_height = sum(heights) + (len(heights) - 1) * usage_spacing if heights else 0
        if total_height <= max_height:
            return font_size, total_height
    
    # Use minimum
    font_size = 28
    heights = []
    for usage in usage_examples:
        if usage.strip():
            usage_text = f'"{usage.strip()}"'
            _, h, _ = _measure_text_dimensions(
                usage_text, 'Baskerville-Italic', font_size
            )
            h = int(h * USAGE_LINE_HEIGHT_MULTIPLIER)
            heights.append(h)
    usage_spacing = int(font_size * 0.8)
    total_height = sum(heights) + (len(heights) - 1) * usage_spacing if heights else 0
    return font_size, total_height


def calculate_provenance_font_size(notes: str, max_height: int, max_width: int = 720) -> Tuple[int, int, List[str]]:
    """
    Calculate provenance font size (24-28pt range).
    Max height: 12% of canvas (≈130px)
    Max lines: 3
    Line height multiplier: 1.3
    Provenance must never feel crushed or glued to the footer.
    """
    if not notes or not notes.strip():
        return 0, 0, []
    
    notes_text = notes.strip()
    PROVENANCE_LINE_HEIGHT_MULTIPLIER = 1.3
    
    for font_size in range(28, 23, -2):  # Try 28, 26, 24
        width, height, lines = _measure_text_dimensions(
            notes_text, ACCENT_FONT, font_size, max_width
        )
        # Apply line height multiplier
        height = int(height * PROVENANCE_LINE_HEIGHT_MULTIPLIER)
        
        # Enforce max 3 lines
        if len(lines) > 3:
            # Truncate to 3 lines with ellipsis
            lines = lines[:3]
            if len(lines) == 3:
                lines[2] = lines[2][:len(lines[2])-3] + "..."
            # Re-measure truncated text
            truncated_text = '\n'.join(lines)
            width, height, _ = _measure_text_dimensions(
                truncated_text, ACCENT_FONT, font_size, max_width
            )
            height = int(height * PROVENANCE_LINE_HEIGHT_MULTIPLIER)
        
        if height <= max_height:
            return font_size, height, lines
    
    # Use minimum
    font_size = 24
    width, height, lines = _measure_text_dimensions(
        notes_text, ACCENT_FONT, font_size, max_width
    )
    height = int(height * PROVENANCE_LINE_HEIGHT_MULTIPLIER)
    if len(lines) > 3:
        lines = lines[:3]
        if len(lines) == 3:
            lines[2] = lines[2][:len(lines[2])-3] + "..."
        truncated_text = '\n'.join(lines)
        width, height, _ = _measure_text_dimensions(
            truncated_text, ACCENT_FONT, font_size, max_width
        )
        height = int(height * PROVENANCE_LINE_HEIGHT_MULTIPLIER)
    return font_size, height, lines


def calculate_proportional_spacing(scots_height: int, translation_height: int, 
                                   usage_height: int, is_short_content: bool = False,
                                   footer_safety_gap: int = 56) -> Dict[str, int]:
    """
    Calculate proportional spacing with proper visual minimums (authoritative clamps).
    
    Rules with clamps:
    - Header → Scots: 0.35 × Scots height (clamped 24-64px)
    - Scots → Translation: 0.30 × Scots height (clamped 48-100px, 60px min for short content)
    - Translation → Usage: 0.30 × Translation height (clamped 42-84px)
    - Usage → Provenance: 0.25 × Usage height (clamped 36-72px)
    - Provenance → Footer: FOOTER_SAFETY_GAP (56px)
    """
    # Header → Scots
    header_to_scots = int(scots_height * 0.35)
    header_to_scots = max(24, min(64, header_to_scots))  # Clamp 24-64px
    
    # Scots → Translation
    scots_to_translation = int(scots_height * 0.30)
    if is_short_content:
        scots_to_translation = max(60, scots_to_translation)  # Minimum 60px for short content
    else:
        scots_to_translation = max(48, min(100, scots_to_translation))  # Clamp 48-100px
    
    # Translation → Usage
    if usage_height > 0:
        translation_to_usage = int(translation_height * 0.30)  # Changed from 0.25
        translation_to_usage = max(42, min(84, translation_to_usage))  # Clamp 42-84px
        
        # Usage → Provenance
        usage_to_provenance = int(usage_height * 0.25)  # Changed from 0.20
        usage_to_provenance = max(36, min(72, usage_to_provenance))  # Clamp 36-72px
    else:
        translation_to_usage = 0
        usage_to_provenance = 0
    
    # Provenance → Footer
    provenance_to_footer = footer_safety_gap  # 56px
    
    return {
        'header_to_scots': header_to_scots,
        'scots_to_translation': scots_to_translation,
        'translation_to_usage': translation_to_usage,
        'usage_to_provenance': usage_to_provenance,
        'provenance_to_footer': provenance_to_footer
    }


def _measure_text_dimensions(text: str, font: str, font_size: int, max_width: int = None) -> Tuple[int, int, List[str]]:
    """
    Measure actual text dimensions using ImageMagick by creating temp image and using identify.
    
    Parameters
    ----------
    text:
        Text to measure
    font:
        Font name (e.g., 'Baskerville-Italic')
    font_size:
        Font size in points
    max_width:
        Maximum width for wrapping (if None, measures single line)
    
    Returns
    -------
    Tuple of (width, height, wrapped_lines)
    - width: Actual rendered width in pixels
    - height: Actual rendered height in pixels (including line spacing)
    - wrapped_lines: List of text lines (wrapped if max_width provided)
    """
    magick_cmd = 'magick' if shutil.which('magick') else 'convert'
    identify_cmd = 'magick' if shutil.which('magick') else 'identify'
    
    if max_width is None:
        # Measure single line - create temp image and measure it
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Create label image
            cmd = [
                magick_cmd,
                '-background', 'transparent',
                '-font', font,
                '-pointsize', str(font_size),
                f'label:{text}',
                temp_path
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            # Measure it
            identify_cmd_list = [
                identify_cmd,
                '-format', '%w %h',
                temp_path
            ]
            result = subprocess.run(identify_cmd_list, capture_output=True, text=True, check=True, timeout=5)
            width, height = map(int, result.stdout.strip().split())
            
            os.unlink(temp_path)
            return width, height, [text]
        except Exception as e:
            logger.warning(f"Error measuring text dimensions: {e}, using fallback")
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            # Fallback: rough estimate
            estimated_width = len(text) * (font_size * 0.6)
            estimated_height = int(font_size * 1.2)
            return int(estimated_width), estimated_height, [text]
    else:
        # Measure with wrapping - calculate line breaks by measuring each potential line
        words = text.split()
        lines = []
        current_line = []
        current_line_text = ""
        
        for word in words:
            test_line = (current_line_text + " " + word).strip() if current_line_text else word
            
            # Measure this potential line by creating temp image
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            try:
                # Create label for this test line
                cmd = [
                    magick_cmd,
                    '-background', 'transparent',
                    '-font', font,
                    '-pointsize', str(font_size),
                    f'label:{test_line}',
                    temp_path
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
                
                # Measure width
                identify_cmd_list = [
                    identify_cmd,
                    '-format', '%w',
                    temp_path
                ]
                result = subprocess.run(identify_cmd_list, capture_output=True, text=True, check=True, timeout=5)
                line_width = int(result.stdout.strip())
                
                os.unlink(temp_path)
                
                if line_width <= max_width or not current_line_text:
                    # Fits on current line (or it's the first word)
                    current_line.append(word)
                    current_line_text = test_line
                else:
                    # Doesn't fit - start new line
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_line_text = word
            except Exception as e:
                logger.warning(f"Error measuring line width for '{test_line}': {e}, using fallback")
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                # Fallback: character-based estimate
                estimated_width = len(test_line) * (font_size * 0.6)
                if estimated_width <= max_width or not current_line_text:
                    current_line.append(word)
                    current_line_text = test_line
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_line_text = word
        
        # Add last line
        if current_line:
            lines.append(' '.join(current_line))
        
        # Measure total height by creating multiline label
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            multiline_text = '\n'.join(lines)
            # Create multiline label
            cmd = [
                magick_cmd,
                '-background', 'transparent',
                '-size', f'{max_width}x' if max_width else '',
                '-font', font,
                '-pointsize', str(font_size),
                f'label:{multiline_text}',
                temp_path
            ]
            if not max_width:
                cmd.remove('-size')
                cmd.remove(f'{max_width}x')
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
            
            # Measure height
            identify_cmd_list = [
                identify_cmd,
                '-format', '%h',
                temp_path
            ]
            result = subprocess.run(identify_cmd_list, capture_output=True, text=True, check=True, timeout=5)
            height = int(result.stdout.strip())
            # Adjust for line spacing
            height = int(height * LINE_HEIGHT_MULTIPLIER)
            
            # Measure width (max of all lines or max_width)
            if max_width:
                width = max_width
            else:
                # Measure each line to get max width
                max_line_width = 0
                for line in lines:
                    temp_line = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_line_path = temp_line.name
                    temp_line.close()
                    try:
                        line_cmd = [
                            magick_cmd,
                            '-background', 'transparent',
                            '-font', font,
                            '-pointsize', str(font_size),
                            f'label:{line}',
                            temp_line_path
                        ]
                        subprocess.run(line_cmd, capture_output=True, text=True, check=True, timeout=5)
                        line_identify = [
                            identify_cmd,
                            '-format', '%w',
                            temp_line_path
                        ]
                        line_result = subprocess.run(line_identify, capture_output=True, text=True, check=True, timeout=5)
                        line_w = int(line_result.stdout.strip())
                        max_line_width = max(max_line_width, line_w)
                        os.unlink(temp_line_path)
                    except:
                        if os.path.exists(temp_line_path):
                            try:
                                os.unlink(temp_line_path)
                            except:
                                pass
                width = max_line_width
            
            os.unlink(temp_path)
            return width, height, lines
        except Exception as e:
            logger.warning(f"Error measuring wrapped text height: {e}, using fallback")
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            # Fallback
            estimated_height = int(font_size * LINE_HEIGHT_MULTIPLIER * len(lines))
            estimated_width = max_width if max_width else max([len(line) * (font_size * 0.6) for line in lines])
            return int(estimated_width), estimated_height, lines


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
    Render square 1080×1080 image using two-tier layout design.
    
    New design principles:
    - Split available space into upper/lower halves (50/50)
    - Upper half: Scots (66%) + Translation (33%)
    - Lower half: Examples (66%) + Provenance (33%) for Words, or just Provenance for Phrases/Insults
    - Fixed font sizes with simple reduction until text fits in area
    - Vertical centering within each area (not top-down flow)
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Verify logo exists (if provided)
        if logo_path and not os.path.exists(logo_path):
            logger.warning(f"Logo file not found at {logo_path}, image will be generated without logo")
            logo_path = None
        
        magick_cmd = 'magick' if shutil.which('magick') else 'convert'
        
        # Canvas constants
        CANVAS_SIZE = 1080
        TOP_MARGIN = 90
        BOTTOM_MARGIN = 90
        
        logger.info("=== Two-Tier Layout Calculation ===")
        
        # Step 1: Measure header (fixed 48pt)
        header_text = title
        _, header_height, _ = _measure_text_dimensions(header_text, HEADER_FONT, HEADER_FONT_SIZE)
        logger.info(f"Header: {header_height}px (fixed 48pt)")
        
        # Step 2: Measure footer (fixed 24pt)
        footer_text = series_footer
        _, footer_height, _ = _measure_text_dimensions(footer_text, ACCENT_FONT, FOOTER_FONT_SIZE)
        logger.info(f"Footer: {footer_height}px (fixed 24pt)")
        
        # Step 3: Compute available region
        available_top = TOP_MARGIN + header_height
        available_bottom = CANVAS_SIZE - BOTTOM_MARGIN - footer_height
        available_height = available_bottom - available_top
        logger.info(f"Available region: top={available_top}px, bottom={available_bottom}px, height={available_height}px")
        
        # Step 4: Split into upper and lower halves (50/50)
        # Upper half: Scots only (positioned high, around 1/4 of page)
        # Lower half: Translation + Examples + Provenance
        upper_height = int(available_height * 0.50)
        lower_height = available_height - upper_height
        
        # Upper half: All for Scots (positioned at top, not centered)
        scots_area_height = upper_height
        
        # Lower half: Translation (top) + Examples (middle) + Provenance (bottom)
        has_examples = (usage_examples and len(usage_examples) > 0) if usage_examples else False
        if has_examples:
            # Word case: Translation + Examples + Provenance
            translation_area_height = int(lower_height * 0.33)  # Top third of lower half
            examples_area_height = int(lower_height * 0.44)  # Middle 44% of lower half
            provenance_area_height = lower_height - translation_area_height - examples_area_height  # Remaining
        else:
            # Phrase/Insult case: Translation + Provenance
            translation_area_height = int(lower_height * 0.50)  # Top half of lower half
            examples_area_height = 0
            provenance_area_height = lower_height - translation_area_height  # Bottom half
        
        logger.info(f"Upper half: {upper_height}px (Scots area: {scots_area_height}px)")
        logger.info(f"Lower half: {lower_height}px (Translation: {translation_area_height}px, Examples: {examples_area_height}px, Provenance: {provenance_area_height}px)")
        
        # Step 5: Measure and fit Scots text (fixed font sizes with reduction)
        # Word: 144pt max (TWICE as big as 72pt - user requested 2x taller)
        # Phrase/Insult: 52pt max
        if category == 'weekly_word':
            initial_scots_size = 144
            min_scots_size = 100
        else:  # phrase or insult
            initial_scots_size = 52
            min_scots_size = 36
        
        scots_font_size = initial_scots_size
        while True:
            _, scots_height, scots_lines = _measure_text_dimensions(
                scots_text, BODY_FONT, scots_font_size, max_width=800
            )
            if scots_height <= scots_area_height or scots_font_size <= min_scots_size:
                break
            scots_font_size -= 2
        
        logger.info(f"Scots: {scots_font_size}pt, height={scots_height}px ({len(scots_lines)} lines)")
        logger.info(f"VERIFY: Scots font size for {category} is {scots_font_size}pt (initial was {initial_scots_size}pt)")
        
        # Step 6: Measure and fit translation
        translation_text = f'→ {translation}'
        # Word: 36pt, Phrase/Insult: 34pt
        initial_trans_size = 36 if category == 'weekly_word' else 34
        trans_font_size = initial_trans_size
        while True:
            _, trans_height, _ = _measure_text_dimensions(
                translation_text, ACCENT_FONT, trans_font_size, max_width=760
            )
            if trans_height <= translation_area_height or trans_font_size <= 30:
                break
            trans_font_size -= 2
        
        logger.info(f"Translation: {trans_font_size}pt, height={trans_height}px")
        
        # Step 7: Measure and fit examples (if any)
        usage_font_size = 0
        total_usage_height = 0
        usage_lines_list = []
        if has_examples:
            ex_font_size = 48  # 50% bigger (was 32pt, now 48pt) - user wants this size
            LINE_SPACING = 25  # Slightly increased spacing for larger font
            # Use 48pt directly - allow it to exceed area if needed (user wants 50% bigger)
            total_ex_height = 0
            usage_lines_list = []
            for ex in usage_examples:
                if ex.strip():
                    usage_text = f'"{ex.strip()}"'
                    _, ex_height, ex_lines = _measure_text_dimensions(
                        usage_text, 'Baskerville-Italic', ex_font_size, max_width=1520  # Twice as wide (was 760)
                    )
                    usage_lines_list.append((usage_text, ex_lines))
                    total_ex_height += ex_height + LINE_SPACING
            total_ex_height -= LINE_SPACING  # Remove last spacing
            usage_font_size = ex_font_size
            total_usage_height = total_ex_height
            
            logger.info(f"Usage: {usage_font_size}pt, height={total_usage_height}px ({len(usage_examples)} examples)")
        else:
            logger.info("Usage: none")
        
        # Step 8: Measure and fit provenance
        provenance_font_size = 0
        provenance_height = 0
        provenance_lines = []
        if notes and notes.strip():
            prov_font_size = 39  # 50% bigger (was 26pt, now 39pt) - user wants this size
            # Use 39pt directly - allow it to exceed area if needed (user wants 50% bigger)
            _, prov_height, prov_lines = _measure_text_dimensions(
                notes.strip(), ACCENT_FONT, prov_font_size, max_width=1440  # Twice as wide (was 720)
            )
            # Enforce max 3 lines
            if len(prov_lines) > 3:
                prov_lines = prov_lines[:3]
                if len(prov_lines) == 3:
                    prov_lines[2] = prov_lines[2][:len(prov_lines[2])-3] + "..."
                # Re-measure truncated
                truncated_text = '\n'.join(prov_lines)
                _, prov_height, _ = _measure_text_dimensions(
                    truncated_text, ACCENT_FONT, prov_font_size, max_width=1440  # Twice as wide (was 720)
                )
            provenance_font_size = prov_font_size
            provenance_height = prov_height
            provenance_lines = prov_lines
            
            logger.info(f"Provenance: {provenance_font_size}pt, height={provenance_height}px ({len(provenance_lines)} lines)")
        else:
            logger.info("Provenance: none")
        
        # Step 9: Compute Y positions
        # Scots: All categories vertically centered in upper half (pushes content lower)
        scots_y = available_top + (scots_area_height - scots_height) // 2
        
        # Translation: In lower half, positioned 100px higher than before
        translation_y = available_top + upper_height + 20 - 100  # Start of lower half + buffer - 100px up
        
        # Examples: Below translation in lower half, moved up 100px
        if has_examples:
            ex_y = available_top + upper_height + translation_area_height + 20 - 100  # Below translation area - 100px up
            prov_y = available_top + upper_height + translation_area_height + examples_area_height + 20 - 100 + 50  # Below examples - 100px up + 50px lower
        else:
            ex_y = 0
            prov_y = available_top + upper_height + translation_area_height + 20 - 100 + 50  # Below translation - 100px up + 50px lower
        
        logger.info(f"Y positions:")
        logger.info(f"  Scots: {scots_y}px (top of upper half, ~1/4 of page)")
        logger.info(f"  Translation: {translation_y}px (lower half, below midpoint)")
        if has_examples:
            logger.info(f"  Examples: {ex_y}px (lower half)")
        logger.info(f"  Provenance: {prov_y}px (lower half)")
        
        # Step 10: Create base canvas
        base_cmd = [
            magick_cmd,
            '-size', f'{CANVAS_SIZE}x{CANVAS_SIZE}',
            f'xc:{BG_COLOR}',
            output_path
        ]
        subprocess.run(base_cmd, capture_output=True, text=True, check=True)
        
        # Step 11: Add header (fixed position)
        header_cmd = [
            magick_cmd,
            output_path,
            '-gravity', 'north',
            '-pointsize', str(HEADER_FONT_SIZE),
            '-font', HEADER_FONT,
            '-fill', HEADER_FOOTER_COLOR,
            '-annotate', f'+0+{TOP_MARGIN}', title,
            output_path
        ]
        subprocess.run(header_cmd, capture_output=True, text=True, check=True)
        
        # Step 12: Add Scots text (centered in area)
        scots_multiline = '\n'.join(scots_lines)
        
        # Create label for Scots text (centered horizontally)
        temp_scots = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_scots_path = temp_scots.name
        temp_scots.close()
        
        # Create label - use caption: for multiline (respects pointsize), label: for single line
        # Width constraint with label: causes auto-scaling, but caption: respects pointsize
        if len(scots_lines) > 1:
            # Multiline: use caption: which wraps and respects pointsize
            scots_label_cmd = [
                magick_cmd,
                '-background', 'transparent',
                '-size', f'{PHRASE_MAX_WIDTH}x',  # Width for wrapping
                '-gravity', 'center',
                '-pointsize', str(scots_font_size),
                '-font', BODY_FONT,
                '-fill', TEXT_COLOR,
                f'caption:{scots_text.replace(chr(34), chr(92)+chr(34)).replace(chr(39), chr(92)+chr(39))}',
                temp_scots_path
            ]
        else:
            # Single line: use label: without size constraint (respects pointsize)
            scots_label_cmd = [
                magick_cmd,
                '-background', 'transparent',
                '-gravity', 'center',
                '-pointsize', str(scots_font_size),
                '-font', BODY_FONT,
                '-fill', TEXT_COLOR,
                f'label:{scots_multiline.replace(chr(34), chr(92)+chr(34)).replace(chr(39), chr(92)+chr(39))}',
                temp_scots_path
            ]
        subprocess.run(scots_label_cmd, capture_output=True, text=True, check=True)
        
        # Composite Scots text - center horizontally, position from top
        scots_composite_cmd = [
            magick_cmd,
            output_path,
            temp_scots_path,
            '-gravity', 'north',  # Position from top, center horizontally
            '-geometry', f'+0+{int(scots_y)}',
            '-composite',
            output_path
        ]
        subprocess.run(scots_composite_cmd, capture_output=True, text=True, check=True)
        os.unlink(temp_scots_path)
        
        # Step 13: Add translation (centered in area)
        translation_cmd = [
            magick_cmd,
            output_path,
            '-gravity', 'north',
            '-pointsize', str(trans_font_size),
            '-font', ACCENT_FONT,
            '-fill', TEXT_COLOR,
            '-annotate', f'+0+{int(translation_y)}', translation_text,
            output_path
        ]
        subprocess.run(translation_cmd, capture_output=True, text=True, check=True)
        
        # Step 14: Add usage examples (if any, centered in area)
        if has_examples and usage_font_size > 0:
            current_usage_y = ex_y
            for usage_text, ex_lines in usage_lines_list:
                usage_multiline = '\n'.join(ex_lines)
                usage_cmd = [
                    magick_cmd,
                    output_path,
                    '-gravity', 'north',
                    '-pointsize', str(usage_font_size),
                    '-font', 'Baskerville-Italic',
                    '-fill', USAGE_COLOR,
                    '-annotate', f'+0+{int(current_usage_y)}', usage_multiline,
                    output_path
                ]
                subprocess.run(usage_cmd, capture_output=True, text=True, check=True)
                # Measure height for next position
                _, usage_h, _ = _measure_text_dimensions(
                    usage_text, 'Baskerville-Italic', usage_font_size, max_width=1520  # Twice as wide (was 760)
                )
                current_usage_y += usage_h + LINE_SPACING
        
        # Step 15: Add provenance/notes (if any, centered in area)
        if provenance_font_size > 0 and provenance_lines:
            provenance_text = '\n'.join(provenance_lines)
            provenance_cmd = [
                magick_cmd,
                output_path,
                '-gravity', 'north',
                '-pointsize', str(provenance_font_size),
                '-font', ACCENT_FONT,
                '-fill', PROVENANCE_COLOR,
                '-annotate', f'+0+{int(prov_y)}', provenance_text,
                output_path
            ]
            subprocess.run(provenance_cmd, capture_output=True, text=True, check=True)
        
        # Step 16: Add footer
        footer_cmd = [
            magick_cmd,
            output_path,
            '-gravity', 'south',
            '-pointsize', str(FOOTER_FONT_SIZE),
            '-fill', HEADER_FOOTER_COLOR,
            '-annotate', f'+0+{BOTTOM_MARGIN}', series_footer,
            output_path
        ]
        subprocess.run(footer_cmd, capture_output=True, text=True, check=True)
        
        # Step 10: Composite logo (if provided)
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
                
                temp_logo = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_logo_path = temp_logo.name
                temp_logo.close()
                
                # Resize logo
                resize_cmd = [
                    magick_cmd,
                    logo_path,
                    '-resize', f'{logo_size}x{logo_size}',
                    temp_logo_path
                ]
                subprocess.run(resize_cmd, capture_output=True, check=True)
                
                # Composite logo
                composite_cmd = [
                    magick_cmd,
                    output_path,
                    temp_logo_path,
                    '-gravity', logo_gravity,
                    '-geometry', f'+{LOGO_PADDING}+{LOGO_PADDING}',
                    '-composite',
                    output_path
                ]
                subprocess.run(composite_cmd, capture_output=True, text=True, check=True)
                os.unlink(temp_logo_path)
                
                # Re-add footer on top of logo
                subprocess.run(footer_cmd, capture_output=True, text=True, check=True)
            except Exception as e:
                logger.warning(f"Logo composite failed: {e}")
        
        # Verify output
        if not os.path.exists(output_path):
            return {
                'success': False,
                'output_path': None,
                'error': f"Output file not created at {output_path}"
            }
        
        file_size = os.path.getsize(output_path)
        if file_size < 1024:
            return {
                'success': False,
                'output_path': output_path,
                'error': f"Output file too small ({file_size} bytes)"
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
        logger.exception("Full exception details:")
        return {
            'success': False,
            'output_path': None,
            'error': error_msg
        }
