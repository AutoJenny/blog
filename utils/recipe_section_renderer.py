"""
Recipe Section Renderer

Converts structured JSON from post_section_elements into beautiful HTML for display.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def convert_to_imperial(metric_value: str) -> str:
    """
    Convert metric weight/volume to approximate imperial (rounded to reasonable values).
    
    Args:
        metric_value: String like "500g", "250ml", "1kg", etc.
        
    Returns:
        Approximate imperial equivalent (rounded, not precise)
    """
    if not metric_value:
        return ""
    
    # Extract number and unit
    match = re.search(r'(\d+(?:\.\d+)?)\s*(g|kg|ml|l|tsp|tbsp)', metric_value.lower())
    if not match:
        return metric_value  # Return as-is if can't parse
    
    value = float(match.group(1))
    unit = match.group(2)
    
    # Convert to imperial with rounding to whole numbers
    if unit == 'g':
        # Grams to ounces (1 oz ≈ 28.35g)
        oz = value / 28.35
        if oz >= 16:
            lbs = oz / 16
            rounded_lbs = round(lbs)
            return f"{rounded_lbs}lb"
        else:
            rounded_oz = round(oz)
            return f"{rounded_oz}oz"
    elif unit == 'kg':
        # Kilograms to pounds (1 kg ≈ 2.2 lb)
        lbs = value * 2.2
        rounded_lbs = round(lbs)
        return f"{rounded_lbs}lb"
    elif unit == 'ml':
        # Milliliters to fluid ounces (1 fl oz ≈ 29.57 ml)
        fl_oz = value / 29.57
        if fl_oz >= 16:
            cups = fl_oz / 8
            rounded_cups = round(cups)
            return f"{rounded_cups} cups"
        else:
            rounded_fl_oz = round(fl_oz)
            return f"{rounded_fl_oz}fl oz"
    elif unit == 'l':
        # Liters to cups/pints (1 L ≈ 4.23 cups, 1 L ≈ 2.11 pints)
        cups = value * 4.23
        if cups >= 2:
            pints = value * 2.11
            rounded_pints = round(pints)
            return f"{rounded_pints}pt"
        else:
            rounded_cups = round(cups)
            return f"{rounded_cups} cups"
    elif unit in ['tsp', 'tbsp']:
        # Teaspoons/tablespoons are the same
        return metric_value
    
    return metric_value


def render_recipe_section(section_type: str, section_elements: dict, draft_content: str = None) -> str:
    """
    Render a recipe section from structured JSON into HTML.
    
    Args:
        section_type: Type of recipe section (recipe_ingredients, recipe_method, etc.)
        section_elements: Structured JSON data from post_section_elements
        draft_content: Fallback HTML content if structured data is not available
        
    Returns:
        HTML string for the section
    """
    if not section_elements:
        # Fallback to draft content if no structured data
        # But filter out any raw JSON that might be in draft content
        if draft_content:
            # Check if draft_content looks like raw JSON (starts with { or [)
            draft_stripped = draft_content.strip()
            if draft_stripped.startswith('{') or draft_stripped.startswith('[') or '```json' in draft_stripped.lower():
                # This is likely raw JSON, don't display it
                return '<p><em>No content available for this section.</em></p>'
        return draft_content or '<p><em>No content available for this section.</em></p>'
    
    if section_type == 'recipe_ingredients':
        return render_ingredients(section_elements)
    elif section_type == 'recipe_method':
        return render_method(section_elements)
    elif section_type == 'recipe_variants':
        return render_variants(section_elements)
    elif section_type == 'recipe_serving':
        return render_serving(section_elements)
    elif section_type == 'recipe_further_reading':
        return render_further_reading(section_elements)
    elif section_type == 'recipe_background':
        # Background section uses draft content, but filter out any raw JSON
        if draft_content:
            # Strip any H2 headings (defensive measure - H2s should only come from section_heading)
            import re
            draft_content = re.sub(r'<h2[^>]*>.*?</h2>', '', draft_content, flags=re.IGNORECASE | re.DOTALL)
            
            draft_stripped = draft_content.strip()
            # Check if draft_content looks like raw JSON (starts with { or [)
            if draft_stripped.startswith('{') or draft_stripped.startswith('[') or '```json' in draft_stripped.lower():
                # This is likely raw JSON, don't display it
                return '<p><em>No content available for this section.</em></p>'
        return draft_content or '<p><em>No content available for this section.</em></p>'
    else:
        # For other recipe sections, use draft content but filter JSON
        if draft_content:
            draft_stripped = draft_content.strip()
            if draft_stripped.startswith('{') or draft_stripped.startswith('[') or '```json' in draft_stripped.lower():
                return '<p><em>No content available for this section.</em></p>'
        return draft_content or '<p><em>No content available for this section.</em></p>'


def render_ingredients(data: dict) -> str:
    """Render ingredients section as a beautiful HTML list."""
    html = []
    
    # Add serves and timing info if available
    if data.get('serves'):
        html.append(f'<div class="recipe-meta"><strong>Serves:</strong> {data["serves"]}</div>')
    
    if data.get('prep_time') or data.get('cook_time'):
        times = []
        if data.get('prep_time'):
            times.append(f'<strong>Prep:</strong> {data["prep_time"]}')
        if data.get('cook_time'):
            times.append(f'<strong>Cook:</strong> {data["cook_time"]}')
        html.append(f'<div class="recipe-meta">{", ".join(times)}</div>')
    
    # Ingredients list
    if data.get('ingredients'):
        html.append('<div class="recipe-ingredients">')
        html.append('<ul class="ingredients-list">')
        
        for ing in data['ingredients']:
            item = ing.get('item', '')
            amount_metric = ing.get('amount_metric', '').strip()
            amount_imperial_raw = ing.get('amount_imperial', '').strip()
            notes = ing.get('notes', '')
            
            # Clean up imperial value - remove "(approx.)" and normalize
            amount_imperial_cleaned = amount_imperial_raw.replace('(approx.)', '').replace('approx.', '').strip() if amount_imperial_raw else ''
            
            # Always convert from metric if we have metric
            # Only use provided imperial if it's actually different from metric (after cleaning)
            if amount_metric:
                # Extract numeric value from metric for comparison
                metric_match = re.search(r'(\d+(?:\.\d+)?)', amount_metric)
                metric_value = metric_match.group(1) if metric_match else None
                
                # Check if imperial is valid and different from metric
                imperial_match = re.search(r'(\d+(?:\.\d+)?)', amount_imperial_cleaned) if amount_imperial_cleaned else None
                imperial_value = imperial_match.group(1) if imperial_match else None
                
                # If imperial is missing, same as metric, or invalid, convert from metric
                if not amount_imperial_cleaned or (metric_value and imperial_value and metric_value == imperial_value):
                    amount_imperial = convert_to_imperial(amount_metric)
                else:
                    # Use cleaned imperial, but ensure it's properly formatted (no decimals, no approx)
                    amount_imperial = amount_imperial_cleaned
                    # Remove any remaining "(approx.)" or "approx" text
                    amount_imperial = re.sub(r'\s*\(?approx\.?\)?\s*', '', amount_imperial, flags=re.IGNORECASE)
                    # Round any decimal values in imperial
                    imperial_num_match = re.search(r'(\d+\.\d+)', amount_imperial)
                    if imperial_num_match:
                        decimal_val = float(imperial_num_match.group(1))
                        rounded_val = round(decimal_val)
                        amount_imperial = amount_imperial.replace(imperial_num_match.group(1), str(rounded_val))
            else:
                amount_imperial = amount_imperial_cleaned if amount_imperial_cleaned else ''
            
            # Format: "smoked haddock (undyed, skinless) — 300g / 11oz"
            parts = []
            
            # Item name first
            if item:
                parts.append(f'<span class="ingredient-item-name">{item}</span>')
            
            # Notes after item
            if notes:
                parts.append(f'<span class="ingredient-notes">({notes})</span>')
            
            # Weights after, in distinct font with inline styles to survive upload
            if amount_metric:
                if amount_imperial and amount_imperial != amount_metric:
                    # Ensure imperial doesn't contain "(approx.)" or similar
                    amount_imperial = re.sub(r'\s*\(?approx\.?\)?\s*', '', amount_imperial, flags=re.IGNORECASE)
                    parts.append(f'<span class="ingredient-amount" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic;"> — {amount_metric} / {amount_imperial}</span>')
                else:
                    parts.append(f'<span class="ingredient-amount" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic;"> — {amount_metric}</span>')
            elif amount_imperial:
                # Clean imperial before displaying
                amount_imperial = re.sub(r'\s*\(?approx\.?\)?\s*', '', amount_imperial, flags=re.IGNORECASE)
                parts.append(f'<span class="ingredient-amount" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic;"> — {amount_imperial}</span>')
            
            html.append(f'<li class="ingredient-item">{" ".join(parts)}</li>')
        
        html.append('</ul>')
        html.append('</div>')
    
    return '\n'.join(html)


def render_method(data: dict) -> str:
    """Render method section as numbered steps."""
    html = []
    
    if data.get('steps'):
        html.append('<div class="recipe-method">')
        html.append('<ol class="method-steps">')
        
        for step in data['steps']:
            number = step.get('number', '')
            instruction = step.get('instruction', '')
            time = step.get('time', '')
            temperature = step.get('temperature', '')
            
            step_html = []
            step_html.append(f'<li class="method-step">')
            step_html.append(f'<div class="step-instruction">{instruction}</div>')
            
            # Add time and temperature if available (with inline styles to survive upload)
            # Note: Font Awesome icons removed as they're not available on clan.com
            meta = []
            if time:
                meta.append(f'<span class="step-time" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic; margin-right: 0.75rem;">{time}</span>')
            if temperature:
                meta.append(f'<span class="step-temperature" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic;">{temperature}</span>')
            
            if meta:
                # Add spacing between instruction and meta, and between time and temperature
                # Use a separator with proper spacing
                separator = ' <span style="margin: 0 0.75rem; color: #9ca3af;">|</span> '
                step_html.append(f'<div class="step-meta" style="margin-top: 0.5rem;">{separator.join(meta)}</div>')
            
            step_html.append('</li>')
            html.append(''.join(step_html))
        
        html.append('</ol>')
        html.append('</div>')
    
    return '\n'.join(html)


def render_variants(data: dict) -> str:
    """Render variants section."""
    html = []
    
    if data.get('variants'):
        html.append('<div class="recipe-variants">')
        
        # Background colors for alternating variants (more distinct)
        variant_backgrounds = [
            '#fef3c7',  # Light yellow
            '#fde68a',  # Medium yellow
            '#fcd34d',  # Darker yellow
        ]
        
        for idx, variant in enumerate(data['variants']):
            name = variant.get('name', '')
            description = variant.get('description', '')
            changes = variant.get('changes', [])
            
            # Use alternating background colors
            bg_color = variant_backgrounds[idx % len(variant_backgrounds)]
            
            html.append(f'<div class="variant-item" style="background: {bg_color}; padding: 1rem; margin-bottom: 0.75rem; border-radius: 6px; border-left: 3px solid #f59e0b;">')
            if name:
                html.append(f'<h4 class="variant-name">{name}</h4>')
            if description:
                # Use same small italic styling as ingredient amounts
                html.append(f'<p class="variant-description" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic; margin-bottom: 0.5rem;">{description}</p>')
            if changes:
                html.append('<ul class="variant-changes">')
                for change in changes:
                    html.append(f'<li>{change}</li>')
                html.append('</ul>')
            html.append('</div>')
        
        html.append('</div>')
    
    return '\n'.join(html)


def render_serving(data: dict) -> str:
    """Render serving suggestions section."""
    html = []
    
    if data.get('serving_suggestions'):
        html.append('<div class="recipe-serving">')
        
        # Background colors for alternating serving suggestions (more distinct)
        serving_backgrounds = [
            '#ecfdf5',  # Light green
            '#d1fae5',  # Medium green
            '#a7f3d0',  # Darker green
        ]
        
        for idx, suggestion in enumerate(data['serving_suggestions']):
            suggestion_type = suggestion.get('type', '')
            description = suggestion.get('description', '')
            accompaniments = suggestion.get('accompaniments', [])
            
            # Use alternating background colors
            bg_color = serving_backgrounds[idx % len(serving_backgrounds)]
            
            html.append(f'<div class="serving-suggestion" style="background: {bg_color}; padding: 1rem; margin-bottom: 0.75rem; border-radius: 6px; border-left: 3px solid #10b981;">')
            if suggestion_type:
                html.append(f'<h4 class="serving-type">{suggestion_type.title()}</h4>')
            if description:
                # Use same small italic styling as ingredient amounts and variant descriptions
                html.append(f'<p class="serving-description" style="font-family: \'Courier New\', monospace; font-size: 0.9em; color: #6b7280; font-weight: 400; font-style: italic; margin-bottom: 0.5rem;">{description}</p>')
            if accompaniments:
                html.append('<ul class="serving-accompaniments">')
                for acc in accompaniments:
                    html.append(f'<li>{acc}</li>')
                html.append('</ul>')
            html.append('</div>')
        
        html.append('</div>')
    
    return '\n'.join(html)


def render_further_reading(data: dict) -> str:
    """Render further reading section."""
    html = []
    
    if data.get('sources'):
        html.append('<div class="recipe-further-reading">')
        html.append('<div class="reading-sources">')
        
        for source in data['sources']:
            title = source.get('title', '')
            url = source.get('url', '')
            why_good = source.get('why_good', '')
            use_case = source.get('use_case', '')
            
            # Use the content from "why_good" or "use_case" as the description
            description = why_good or use_case or ''
            
            html.append('<div class="source-item">')
            if title and url:
                html.append(f'<h4><a href="{url}" target="_blank" rel="noopener">{title}</a></h4>')
            elif title:
                html.append(f'<h4>{title}</h4>')
            
            if description:
                html.append(f'<p class="source-description">{description}</p>')
            
            html.append('</div>')
        
        html.append('</div>')
        html.append('</div>')
    
    return '\n'.join(html)
