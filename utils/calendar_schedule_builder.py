# c3_json_builder.py
# Utility: JSON Builder for Calendar Scheduling System

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from config.database import db_manager
from utils.calendar_resolver import get_category_config, get_cycle_start_week, resolve_item_for_week

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
    "weekly_insult",
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
        # For profile types, we need to JOIN with post table to get title
        title_col = None  # Will be handled via JOIN
        desc_col = None
    elif original_category in ("weekly_word", "weekly_phrase", "weekly_insult"):
        title_col = "idea_title"
        desc_col = "idea_description"
    else:
        title_col = None
        desc_col = None
    
    try:
        with db_manager.get_cursor() as cursor:
            # For profile types, JOIN with post table to get title
            if original_category in ("profile_product", "profile_surname"):
                sql = f"""
                    SELECT cps.{id_col}, cps.{pos_col}, p.title
                    FROM {table} cps
                    LEFT JOIN post p ON cps.post_id = p.id
                """
                params: List[Any] = []
                
                if extra_filter:
                    cond, extra_params = extra_filter
                    # Qualify profile_type with table alias to avoid ambiguity
                    cond = cond.replace("profile_type", "cps.profile_type")
                    sql += f" WHERE {cond}"
                    params.extend(extra_params)
                
                sql += f" ORDER BY cps.{pos_col} ASC"
                
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    item = {
                        "id": row[id_col],
                        "position": row[pos_col],
                    }
                    # Get title from post table
                    post_title = row.get("title")
                    if post_title:
                        item["title"] = post_title
                    result.append(item)
                
                return result
            else:
                # For non-profile types, use standard query
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
    
    NOW USES: resolve_item_for_week() to ensure consistency with all views.
    This includes overrides automatically, ensuring JSON files match what the resolver returns.
    
    `items` parameter is kept for backward compatibility but is no longer used.
    The resolver handles base lists and overrides internally.
    
    Returns path to written JSON file.
    """
    result = []
    
    # Use unified resolver for each week to ensure consistency
    # This includes overrides automatically
    for w in range(1, 53):
        resolved_item = resolve_item_for_week(category, year, w)
        
        if resolved_item:
            # Extract the appropriate ID field based on category
            item_id = None
            if category == "theme":
                item_id = resolved_item.get("id")
            elif category == "recipe":
                item_id = resolved_item.get("id")
            elif category in ("profile_product", "profile_surname"):
                item_id = resolved_item.get("post_id")  # Profiles use post_id
            elif category in ("weekly_word", "weekly_phrase", "weekly_insult"):
                item_id = resolved_item.get("id")
            
            # Extract title based on category
            title = ""
            if category == "theme":
                title = resolved_item.get("theme_title", "")
            elif category == "recipe":
                title = resolved_item.get("recipe_title", "")
            elif category in ("profile_product", "profile_surname"):
                # For profiles, we need to fetch title from post table
                if item_id:
                    try:
                        with db_manager.get_cursor() as cursor:
                            cursor.execute("SELECT title FROM post WHERE id = %s", (item_id,))
                            post_row = cursor.fetchone()
                            if post_row:
                                title = post_row.get("title", "") if isinstance(post_row, dict) else post_row[0] if post_row else ""
                    except Exception as e:
                        logger.warning(f"Error fetching post title for profile {item_id}: {e}")
            elif category in ("weekly_word", "weekly_phrase", "weekly_insult"):
                title = resolved_item.get("idea_title", "")
            
            entry = {
                "week": w,
                "item_id": item_id,
                "position": resolved_item.get("position"),  # Store actual position
                "title": title
            }
            # Include description if available
            if category == "theme" and resolved_item.get("theme_description"):
                entry["description"] = resolved_item.get("theme_description")
            elif category == "recipe" and resolved_item.get("recipe_description"):
                entry["description"] = resolved_item.get("recipe_description")
            elif category in ("weekly_word", "weekly_phrase", "weekly_insult") and resolved_item.get("idea_description"):
                entry["description"] = resolved_item.get("idea_description")
            
            # Mark if this was an override
            if resolved_item.get("_override"):
                entry["_override"] = True
        else:
            # No item for this week (empty list)
            entry = {"week": w, "item_id": None, "position": None, "title": None}
        
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
