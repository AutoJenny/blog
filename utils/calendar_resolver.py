"""
Calendar Resolver - Shared utility for cyclic calendar resolution

This module centralizes:
- Category → table mapping
- Position-based lookup
- Override handling
- Week resolution
"""

import logging
from typing import Optional, Dict, Any
from config.database import db_manager

logger = logging.getLogger(__name__)


def get_category_config(category: str, classification: str | None = None) -> dict:
    """
    Returns configuration for a given category, including:
      - table name
      - id column
      - position column
      - optional extra WHERE clause and params
    
    Supports both old naming (profile_product, profile_category, profile_surname)
    and new naming (profile with classification parameter).
    """
    if not isinstance(category, str):
        raise ValueError("category must be a string")
    category = category.strip().lower()
    
    # Handle old profile naming convention
    if category in ("profile_product", "profile_category", "profile_surname"):
        profile_type = category.replace("profile_", "")
        category = "profile"
        classification = profile_type
    
    if category == "theme":
        return {
            "table": "calendar_themes",
            "id_column": "id",
            "position_column": "position",
            "extra_filter": None,
        }
    
    if category == "recipe":
        return {
            "table": "calendar_recipes",
            "id_column": "id",
            "position_column": "position",
            "extra_filter": None,
        }
    
    if category == "profile":
        if not classification:
            raise ValueError("classification (profile_type) is required for category 'profile'")
        return {
            "table": "calendar_profile_sequence",
            "id_column": "post_id",
            "position_column": "position",
            "extra_filter": ("profile_type = %s", [classification]),
        }
    
    if category in ("weekly_word", "weekly_phrase"):
        if not classification:
            classification = category
        return {
            "table": "calendar_ideas",
            "id_column": "id",
            "position_column": "position",
            "extra_filter": ("item_classification = %s", [classification]),
        }
    
    raise ValueError(f"Unknown category: {category}")


def get_cycle_start_week(category: str) -> int:
    """
    Return cycle_start_week from calendar_category_cycles.
    Defaults to 1 if not set.
    
    NOTE: The 'category' key here must match what you store in
    calendar_category_cycles.category (e.g. 'theme', 'recipe',
    'profile_product', 'weekly_word', etc.).
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT cycle_start_week
                FROM calendar_category_cycles
                WHERE category = %s
                """,
                (category,),
            )
            row = cursor.fetchone()
            if not row or row.get("cycle_start_week") is None:
                return 1
            return int(row["cycle_start_week"])
    except Exception as e:
        logger.error("Error getting cycle start week for %s: %s", category, e)
        return 1


def get_list_length(category: str, classification: str | None = None) -> int:
    """
    Count how many items are in the cyclic list for a given category.
    """
    cfg = get_category_config(category, classification)
    table = cfg["table"]
    extra_filter = cfg["extra_filter"]
    
    try:
        with db_manager.get_cursor() as cursor:
            sql = f"SELECT COUNT(*) AS cnt FROM {table}"
            params: list[Any] = []
            
            if extra_filter:
                cond, extra_params = extra_filter
                sql += f" WHERE {cond}"
                params.extend(extra_params)
            
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()
            return int(row["cnt"] or 0) if row else 0
    except Exception as e:
        logger.error("Error getting list length for %s: %s", category, e)
        return 0


def get_item_by_position(
    category: str,
    position: int,
    classification: str | None = None,
) -> Optional[Dict[str, Any]]:
    """
    Return the row for a given position.
    """
    cfg = get_category_config(category, classification)
    table = cfg["table"]
    pos_col = cfg["position_column"]
    extra_filter = cfg["extra_filter"]
    
    try:
        with db_manager.get_cursor() as cursor:
            sql = f"SELECT * FROM {table} WHERE {pos_col} = %s"
            params: list[Any] = [position]
            
            if extra_filter:
                cond, extra_params = extra_filter
                sql += f" AND {cond}"
                params.extend(extra_params)
            
            cursor.execute(sql, tuple(params))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    except Exception as e:
        logger.error(
            "Error getting item by position for %s position %s: %s",
            category,
            position,
            e,
        )
        return None


def get_week_override(category: str, year: int, week: int) -> Optional[Dict[str, Any]]:
    """
    Return override row for (year, week, category) if present.
    
    'category' here must match the value stored by the API:
    e.g. 'theme', 'recipe', 'profile_product', 'profile_surname',
    'weekly_word', 'weekly_phrase'.
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM calendar_week_overrides
                WHERE year = %s AND week_number = %s AND category = %s
                """,
                (year, week, category),
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    except Exception as e:
        logger.error(
            "Error getting week override for %s week %s-W%s: %s",
            category,
            year,
            week,
            e,
        )
        return None


def _to_int(value, name: str) -> int:
    """
    Internal helper to coerce year/week to int defensively.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer (got {value!r})")


def resolve_item_for_week(
    category: str,
    year: int,
    week: int,
    classification: str | None = None,
) -> Optional[Dict[str, Any]]:
    """
    Resolve the item for (year, week, category), taking overrides into account.
    
    Supports both old naming (profile_product, profile_category, profile_surname)
    and new naming (profile with classification parameter).
    
    Returns:
      - mapping/dict for the row (from the cyclic table), or
      - None if the list is empty.
    
    Behaviour:
      1. Look for a row in calendar_week_overrides using the SAME category key
         that is stored there (e.g. 'theme', 'profile_product', 'weekly_word').
      2. If found, fetch that item by ID from the appropriate list table and
         mark it with _override = True.
      3. If not found, compute the cyclic position and fetch the item,
         marking _override = False and _position = computed slot.
    """
    if not isinstance(category, str):
        raise ValueError("category must be a string")
    # Normalised names:
    # - original_category: the EXACT label used in overrides and cycles table
    # - normalized_category: the internal category used to locate the correct table
    original_category = category.strip().lower()
    normalized_category = original_category
    
    # Profiles: keep override key as 'profile_product' / 'profile_surname',
    # but resolve data from the underlying 'profile' sequence with classification.
    if original_category in ("profile_product", "profile_category", "profile_surname"):
        profile_type = original_category.replace("profile_", "")
        normalized_category = "profile"
        classification = profile_type
    elif original_category == "profile" and classification:
        # For the cycles table and overrides we still store e.g. 'profile_product'
        original_category = f"profile_{classification}"
    
    # Strong typing for year/week
    year_int = _to_int(year, "year")
    week_int = _to_int(week, "week")
    
    # 1. Check override (use original_category as stored in DB)
    override = get_week_override(original_category, year_int, week_int)
    if override:
        cfg = get_category_config(normalized_category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        extra_filter = cfg["extra_filter"]
        
        try:
            with db_manager.get_cursor() as cursor:
                sql = f"SELECT * FROM {table} WHERE {id_col} = %s"
                params: list[Any] = [override["item_id"]]
                
                if extra_filter:
                    cond, extra_params = extra_filter
                    sql += f" AND {cond}"
                    params.extend(extra_params)
                
                cursor.execute(sql, tuple(params))
                row = cursor.fetchone()
                
                if row:
                    result = dict(row)
                    result["_override"] = True
                    # Expose the underlying list position as well for debugging/UI
                    if "position" in result:
                        result["_position"] = result["position"]
                    return result
        except Exception as e:
            logger.error("Error resolving override item for %s: %s", category, e)
    
    # 2. Use cyclic formula (use normalized_category)
    N = get_list_length(normalized_category, classification)
    if N == 0:
        return None
    
    # For cycle_start_week we also use the override/cycle key (original_category)
    cycle_start = get_cycle_start_week(original_category)
    
    # absolute_week here is simply the week number; if you want multi-year rolling,
    # you may compute a different absolute index. For now: use week directly.
    absolute_week = week_int
    pos = ((absolute_week - cycle_start) % N) + 1
    
    item = get_item_by_position(normalized_category, pos, classification=classification)
    if item:
        item["_override"] = False
        item["_position"] = pos
    return item


def build_year_schedule(year: int, weeks: int = 52) -> list[dict]:
    """
    Build schedule for all weeks of a given year.
    
    Returns a list of dicts:
      {
        "week": n,
        "theme": {...},
        "recipe": {...},
        "profile": {...},
        "weekly_word": {...},
        "weekly_phrase": {...}
      }
    """
    result: list[dict] = []
    year_int = _to_int(year, "year")
    
    for week in range(1, weeks + 1):
        week_entry: dict[str, Any] = {"week": week}
        
        # Themes
        theme = resolve_item_for_week("theme", year_int, week)
        if theme:
            week_entry["theme"] = {
                "id": theme.get("id"),
                "title": theme.get("theme_title"),
                # Use DB position; for override we also exposed _position
                "position": theme.get("position"),
            }
        else:
            week_entry["theme"] = None
        
        # Recipes
        recipe = resolve_item_for_week("recipe", year_int, week)
        if recipe:
            week_entry["recipe"] = {
                "id": recipe.get("id"),
                "title": recipe.get("recipe_title"),
                "position": recipe.get("position"),
            }
        else:
            week_entry["recipe"] = None
        
        # Profiles - resolve for each type separately to match existing frontend expectations
        profile_product = resolve_item_for_week("profile_product", year_int, week)
        profile_category = resolve_item_for_week("profile_category", year_int, week)
        profile_surname = resolve_item_for_week("profile_surname", year_int, week)
        
        # Return the first available profile, or structure as needed
        if profile_product:
            week_entry["profile"] = {
                "id": profile_product.get("post_id"),
                "profile_type": "product",
                "position": profile_product.get("position"),
            }
        elif profile_category:
            week_entry["profile"] = {
                "id": profile_category.get("post_id"),
                "profile_type": "category",
                "position": profile_category.get("position"),
            }
        elif profile_surname:
            week_entry["profile"] = {
                "id": profile_surname.get("post_id"),
                "profile_type": "surname",
                "position": profile_surname.get("position"),
            }
        else:
            week_entry["profile"] = None
        
        # Weekly word
        ww = resolve_item_for_week("weekly_word", year_int, week, classification="weekly_word")
        if ww:
            week_entry["weekly_word"] = {
                "id": ww.get("id"),
                "title": ww.get("idea_title"),
                "position": ww.get("position"),
            }
        else:
            week_entry["weekly_word"] = None
        
        # Weekly phrase
        wp = resolve_item_for_week("weekly_phrase", year_int, week, classification="weekly_phrase")
        if wp:
            week_entry["weekly_phrase"] = {
                "id": wp.get("id"),
                "title": wp.get("idea_title"),
                "position": wp.get("position"),
            }
        else:
            week_entry["weekly_phrase"] = None
        
        result.append(week_entry)
    
    return result
