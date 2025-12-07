# c3_json_builder.py
# Utility: JSON Builder for Calendar Scheduling System

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from config.database import db_manager
from utils.calendar_resolver import get_category_config, get_cycle_start_week

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data", "calendar", "schedule")

CATEGORIES = [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase",
]


def ensure_dir(path):
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)


def _load_base_list_items(category: str) -> List[Dict[str, Any]]:
    """Load base list items from database for a category."""
    # Normalize category for resolver
    original_category = category
    classification = None
    
    # Handle profile categories
    if category in ("profile_product", "profile_surname"):
        profile_type = category.replace("profile_", "")
        category = "profile"
        classification = profile_type
    
    # Get category config
    try:
        config = get_category_config(category, classification)
    except ValueError as e:
        logger.error("Unknown category: %s", original_category)
        raise
    
    table = config["table"]
    id_col = config["id_column"]
    pos_col = config["position_column"]
    extra_filter = config["extra_filter"]
    
    # Determine title and description columns
    if original_category == "theme":
        title_col = "theme_title"
        desc_col = "theme_description"
    elif original_category == "recipe":
        title_col = "recipe_title"
        desc_col = "recipe_description"
    elif original_category in ("profile_product", "profile_surname"):
        title_col = None
        desc_col = None
    elif original_category in ("weekly_word", "weekly_phrase"):
        title_col = "idea_title"
        desc_col = "idea_description"
    else:
        title_col = None
        desc_col = None
    
    try:
        with db_manager.get_cursor() as cursor:
            select_cols = [id_col, pos_col]
            if title_col:
                select_cols.append(title_col)
            if desc_col:
                select_cols.append(desc_col)
            
            sql = f"SELECT {', '.join(select_cols)} FROM {table}"
            params: List[Any] = []
            
            if extra_filter:
                cond, extra_params = extra_filter
                sql += f" WHERE {cond}"
                params.extend(extra_params)
            
            sql += f" ORDER BY {pos_col} ASC"
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                item = {
                    "id": row[id_col],
                    "position": row[pos_col],
                }
                if title_col and row.get(title_col):
                    item["title"] = row[title_col]
                if desc_col and row.get(desc_col):
                    item["description"] = row[desc_col]
                result.append(item)
            
            return result
    except Exception as e:
        logger.error("Error loading base list for category=%s: %s", original_category, e)
        raise


def build_year(category: str, year: int, items: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Build 52-week JSON schedule for a given category and year.
    
    `items` should be the cyclic base list (already ordered).
    If None, loads from database.
    
    Returns path to written JSON file.
    """
    if items is None:
        items = _load_base_list_items(category)
    
    result = []
    N = len(items)
    
    # Get cycle start week (defaults to 1)
    cycle_start_week = get_cycle_start_week(category)
    
    if N == 0:
        # Produce 52 empty weeks
        for w in range(1, 53):
            result.append({"week": w, "item_id": None, "position": None, "title": None})
    else:
        for w in range(1, 53):
            # Cyclic formula: pos = ((w - cycle_start_week) mod N) + 1
            offset = (w - cycle_start_week) % N
            if offset < 0:
                offset += N
            pos = offset + 1
            
            # Find item at this position
            item = next((it for it in items if it.get("position") == pos), None)
            
            if item:
                entry = {
                    "week": w,
                    "item_id": item.get("id"),
                    "position": item.get("position"),
                    "title": item.get("title", "")
                }
                # Include description if available
                if item.get("description"):
                    entry["description"] = item["description"]
            else:
                entry = {
                    "week": w,
                    "item_id": None,
                    "position": None,
                    "title": None
                }
            
            result.append(entry)
    
    # Determine output path (directory-per-category layout)
    category_dir = os.path.join(DATA_DIR, category)
    ensure_dir(category_dir)
    
    filename = f"{year}.json"
    path = os.path.join(category_dir, filename)
    
    # Write JSON file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info("Built schedule JSON: category=%s year=%s path=%s", category, year, path)
    return path


def build_all_categories(year: int, base_lists: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, str]:
    """
    Build all categories for a given year.
    
    base_lists: {category: list_of_items} - if None, loads from DB
    Returns: {category: file_path}
    """
    paths = {}
    
    for category in CATEGORIES:
        try:
            items = None
            if base_lists and category in base_lists:
                items = base_lists[category]
            
            p = build_year(category, year, items)
            paths[category] = p
        except Exception as e:
            logger.error("Error building category=%s year=%s: %s", category, year, e)
    
    return paths
