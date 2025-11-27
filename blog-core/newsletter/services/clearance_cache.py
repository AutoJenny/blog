"""Service for caching scraped clearance product data temporarily."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path

def get_cache_file_path() -> str:
    """Get standard temp file path for clearance data.
    
    Returns:
        Path to temp file: temp/newsletter_clearance_products_YYYYMMDD_HHMMSS.json
    """
    # Get project root (this file is in blog-core/newsletter/services/, go up 3 levels)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    temp_dir = project_root / 'temp'
    temp_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'newsletter_clearance_products_{timestamp}.json'
    return str(temp_dir / filename)


def save_clearance_data(products: List[Dict[str, Any]]) -> str:
    """Save scraped clearance products to temporary file.
    
    Args:
        products: List of product dicts with url, image_url, title, price_now, price_was, etc.
    
    Returns:
        Path to saved file
    """
    file_path = get_cache_file_path()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    return file_path


def load_clearance_data(file_path: str) -> List[Dict[str, Any]]:
    """Load clearance products from temporary file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        List of product dicts
    """
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

