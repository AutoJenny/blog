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
    else:
        # For recipe_background or other sections, use draft content
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
        html.append('<h3>Ingredients</h3>')
        html.append('<ul class="ingredients-list">')
        
        for ing in data['ingredients']:
            item = ing.get('item', '')
            amount_metric = ing.get('amount_metric', '')
            amount_imperial = ing.get('amount_imperial', '')
            notes = ing.get('notes', '')
            
            # Always show both metric and imperial if metric is present
            # If imperial not provided or same as metric, convert from metric
            if amount_metric:
                if not amount_imperial or amount_imperial == amount_metric:
                    amount_imperial = convert_to_imperial(amount_metric)
            
            # Format: "smoked haddock (undyed, skinless) — 300g / 11oz approx"
            parts = []
            
            # Item name first
            if item:
                parts.append(f'<span class="ingredient-item-name">{item}</span>')
            
            # Notes after item
            if notes:
                parts.append(f'<span class="ingredient-notes">({notes})</span>')
            
            # Weights after, in distinct font
            if amount_metric:
                if amount_imperial and amount_imperial != amount_metric:
                    parts.append(f'<span class="ingredient-amount"> — {amount_metric} / {amount_imperial}</span>')
                else:
                    parts.append(f'<span class="ingredient-amount"> — {amount_metric}</span>')
            elif amount_imperial:
                parts.append(f'<span class="ingredient-amount"> — {amount_imperial}</span>')
            
            html.append(f'<li class="ingredient-item">{" ".join(parts)}</li>')
        
        html.append('</ul>')
        html.append('</div>')
    
    return '\n'.join(html)


def render_method(data: dict) -> str:
    """Render method section as numbered steps."""
    html = []
    
    if data.get('steps'):
        html.append('<div class="recipe-method">')
        html.append('<h3>Method</h3>')
        html.append('<ol class="method-steps">')
        
        for step in data['steps']:
            number = step.get('number', '')
            instruction = step.get('instruction', '')
            time = step.get('time', '')
            temperature = step.get('temperature', '')
            
            step_html = []
            step_html.append(f'<li class="method-step">')
            step_html.append(f'<div class="step-instruction">{instruction}</div>')
            
            # Add time and temperature if available
            meta = []
            if time:
                meta.append(f'<span class="step-time"><i class="fas fa-clock"></i> {time}</span>')
            if temperature:
                meta.append(f'<span class="step-temperature"><i class="fas fa-thermometer-half"></i> {temperature}</span>')
            
            if meta:
                step_html.append(f'<div class="step-meta">{" ".join(meta)}</div>')
            
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
        html.append('<h3>Variations</h3>')
        
        for variant in data['variants']:
            name = variant.get('name', '')
            description = variant.get('description', '')
            changes = variant.get('changes', [])
            
            html.append('<div class="variant-item">')
            if name:
                html.append(f'<h4 class="variant-name">{name}</h4>')
            if description:
                html.append(f'<p class="variant-description">{description}</p>')
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
        html.append('<h3>Serving Suggestions</h3>')
        
        for suggestion in data['serving_suggestions']:
            suggestion_type = suggestion.get('type', '')
            description = suggestion.get('description', '')
            accompaniments = suggestion.get('accompaniments', [])
            
            html.append('<div class="serving-suggestion">')
            if suggestion_type:
                html.append(f'<h4 class="serving-type">{suggestion_type.title()}</h4>')
            if description:
                html.append(f'<p class="serving-description">{description}</p>')
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
        html.append('<h3>Further Reading</h3>')
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
