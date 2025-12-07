"""
Planning Calendar API - Override / Reassignment Layer

Provides endpoints for managing week-level overrides that allow moving items
between weeks without modifying base cyclic lists.

This layer sits on top of the JSON-backed calendar display and allows
week-to-week reassignments while keeping base lists intact.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from datetime import datetime
import logging

from utils.calendar_resolver import get_category_config, get_cycle_start_week

logger = logging.getLogger(__name__)

bp = Blueprint("planning_api_calendar_overrides", __name__, url_prefix="/planning")

# Supported categories (must match list management and JSON builder)
SUPPORTED_CATEGORIES = [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase",
]


def json_error(message, status=400):
    """Return standardized error response."""
    return jsonify({"success": False, "error": message}), status


def get_json():
    """Get and validate JSON request body."""
    if not request.is_json:
        raise ValueError("Request must be JSON")
    return request.get_json()


def _to_int(value, field_name):
    """Strictly coerce a JSON field to int, with a clear error if invalid."""
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")


@bp.route("/api/calendar/list/get", methods=["GET"])
def api_list_get():
    """
    Return the current cyclic list for a category.

    Query params:
        category: logical category name (required)
        classification: optional classification for some categories

    Response JSON (success):
        {
            "status": "ok",
            "category": "theme",
            "items": [
                {
                    "id": 101,
                    "position": 1,
                    "title": "Theme 1",
                    "raw": { ...full row... }
                },
                ...
            ]
        }
    """
    try:
        category = request.args.get("category", type=str)
        classification = request.args.get("classification", type=str)

        if not category:
            return json_error("category query parameter is required")

        cfg = get_category_config(category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        pos_col = cfg["position_column"]
        extra_filter = cfg["extra_filter"]

        items = []
        with db_manager.get_cursor() as cursor:
            sql = f"SELECT * FROM {table}"
            params = []

            if extra_filter:
                cond, extra_params = extra_filter
                sql += f" WHERE {cond}"
                params.extend(extra_params)

            sql += f" ORDER BY {pos_col} ASC"

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall() or []

            for row in rows:
                row_dict = dict(row)
                item_id = row_dict.get(id_col)
                position = row_dict.get(pos_col)

                # Derive a human-friendly title based on category
                cat = category.strip().lower()
                if cat == "theme":
                    title = row_dict.get("theme_title") or f"Theme #{item_id}"
                elif cat == "recipe":
                    title = row_dict.get("recipe_title") or f"Recipe #{item_id}"
                elif cat.startswith("profile"):
                    post_id = row_dict.get("post_id")
                    title = f"Profile #{post_id or item_id}"
                elif cat in ("weekly_word", "weekly_phrase"):
                    title = row_dict.get("idea_title") or f"Idea #{item_id}"
                else:
                    title = f"Item #{item_id}"

                items.append(
                    {
                        "id": item_id,
                        "position": position,
                        "title": title,
                        "raw": row_dict,
                    }
                )

        # Get metadata: list_length and cycle_start_week
        list_length = len(items)
        
        # Get cycle_start_week from calendar_category_cycles table
        # Use original category name for cycle lookup
        original_category = category
        cycle_start_week = get_cycle_start_week(original_category)
        
        # Build response with meta object
        response_data = {
            "status": "ok",
            "category": category,
            "items": items,
            "meta": {
                "list_length": list_length,
                "cycle_start_week": cycle_start_week
            }
        }
        
        return jsonify(response_data)

    except ValueError as e:
        return json_error(str(e))
    except Exception:
        logger.exception("Error in api_list_get")
        return json_error("Internal server error", status=500)


def _validate_week(week: int):
    """Validate week number is in valid range."""
    if week < 1 or week > 52:
        raise ValueError("week must be between 1 and 52")
    return week


def _validate_item_exists(category: str, item_id: int, classification: str | None = None) -> bool:
    """
    Validate that an item_id exists in the base table for the category.
    
    Returns True if valid, False otherwise.
    """
    try:
        # Normalize category for profile types
        normalized_category = category
        if category in ("profile_product", "profile_surname"):
            profile_type = category.replace("profile_", "")
            normalized_category = "profile"
            classification = profile_type
        
        cfg = get_category_config(normalized_category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        extra_filter = cfg["extra_filter"]
        
        with db_manager.get_cursor() as cursor:
            sql = f"SELECT 1 FROM {table} WHERE {id_col} = %s"
            params = [item_id]
            
            if extra_filter:
                cond, extra_params = extra_filter
                sql += f" AND {cond}"
                params.extend(extra_params)
            
            cursor.execute(sql, tuple(params))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error("Error validating item_id=%s for category=%s: %s", item_id, category, e)
        return False


def _rebuild_category_year_json(category: str, year: int):
    """
    Trigger JSON rebuild for a specific category/year after override change.
    
    Args:
        category: Category name (e.g., "theme", "profile_product")
        year: ISO year
    """
    try:
        from utils.calendar_schedule_builder import write_category_year_json
        
        write_category_year_json(category, year)
        logger.info(
            "Rebuilt JSON for category=%s year=%s after override change",
            category,
            year,
        )
    except ImportError:
        logger.warning(
            "Could not import calendar_schedule_builder; JSON rebuild skipped"
        )
    except Exception as e:
        logger.error(
            "Error rebuilding JSON for category=%s year=%s: %s",
            category,
            year,
            e,
        )
        # Don't fail the override operation if rebuild fails
        raise


# ---------------------------------------------------------------------------
# OVERRIDE SET
# POST /planning/api/calendar/override/set
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/override/set", methods=["POST"])
def api_override_set():
    """
    Set an override for a specific (category, year, week) to use a specific item_id.
    
    Request JSON:
    {
        "category": "theme",
        "year": 2025,
        "week": 12,
        "item_id": 131
    }
    
    Response JSON (success):
    {
        "success": true,
        "category": "theme",
        "year": 2025,
        "week": 12,
        "item_id": 131
    }
    """
    try:
        data = get_json()
        category = data.get("category")
        year_raw = data.get("year")
        week_raw = data.get("week")
        item_id_raw = data.get("item_id")
        
        # Validation
        if not category:
            return json_error("category is required")
        if category not in SUPPORTED_CATEGORIES:
            return json_error(
                f"Unknown category: {category}. Supported: {', '.join(SUPPORTED_CATEGORIES)}"
            )
        if year_raw is None:
            return json_error("year is required")
        if week_raw is None:
            return json_error("week is required")
        if item_id_raw is None:
            return json_error("item_id is required")
        
        year = _to_int(year_raw, "year")
        week = _validate_week(_to_int(week_raw, "week"))
        item_id = _to_int(item_id_raw, "item_id")
        
        # Validate item exists in base table
        if not _validate_item_exists(category, item_id):
            return json_error(
                f"item_id {item_id} does not exist in base list for category {category}",
                status=404,
            )
        
        # Save or update override
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                now = datetime.utcnow()
                
                # Upsert override
                sql = """
                    INSERT INTO calendar_week_overrides 
                        (year, week_number, category, item_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (year, week_number, category)
                    DO UPDATE SET 
                        item_id = EXCLUDED.item_id,
                        updated_at = EXCLUDED.updated_at
                """
                
                cursor.execute(sql, (year, week, category, item_id, now, now))
                conn.commit()
        
        # Rebuild JSON for this category/year
        try:
            _rebuild_category_year_json(category, year)
        except Exception as e:
            logger.error(
                "Override set successfully but JSON rebuild failed: %s", e
            )
            # Still return success - override is saved, JSON can be rebuilt manually
        
        return jsonify(
            {
                "success": True,
                "category": category,
                "year": year,
                "week": week,
                "item_id": item_id,
            }
        )
    
    except ValueError as e:
        logger.warning("Validation error in api_override_set: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_override_set")
        return json_error("Internal server error", status=500)


# ---------------------------------------------------------------------------
# OVERRIDE REMOVE
# POST /planning/api/calendar/override/remove
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/override/remove", methods=["POST"])
def api_override_remove():
    """
    Remove an override for a specific (category, year, week), reverting to cyclic item.
    
    Request JSON:
    {
        "category": "theme",
        "year": 2025,
        "week": 12
    }
    
    Response JSON (success):
    {
        "success": true,
        "category": "theme",
        "year": 2025,
        "week": 12
    }
    """
    try:
        data = get_json()
        category = data.get("category")
        year_raw = data.get("year")
        week_raw = data.get("week")
        
        # Validation
        if not category:
            return json_error("category is required")
        if category not in SUPPORTED_CATEGORIES:
            return json_error(
                f"Unknown category: {category}. Supported: {', '.join(SUPPORTED_CATEGORIES)}"
            )
        if year_raw is None:
            return json_error("year is required")
        if week_raw is None:
            return json_error("week is required")
        
        year = _to_int(year_raw, "year")
        week = _validate_week(_to_int(week_raw, "week"))
        
        # Delete override
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                    DELETE FROM calendar_week_overrides
                    WHERE year = %s AND week_number = %s AND category = %s
                """
                
                cursor.execute(sql, (year, week, category))
                deleted_count = cursor.rowcount
                conn.commit()
        
        if deleted_count == 0:
            # Override didn't exist - still return success (idempotent)
            logger.debug(
                "Override remove called for non-existent override: category=%s year=%s week=%s",
                category,
                year,
                week,
            )
        else:
            # Rebuild JSON for this category/year
            try:
                _rebuild_category_year_json(category, year)
            except Exception as e:
                logger.error(
                    "Override removed successfully but JSON rebuild failed: %s", e
                )
                # Still return success - override is removed, JSON can be rebuilt manually
        
        return jsonify(
            {
                "success": True,
                "category": category,
                "year": year,
                "week": week,
            }
        )
    
    except ValueError as e:
        logger.warning("Validation error in api_override_remove: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_override_remove")
        return json_error("Internal server error", status=500)


# ---------------------------------------------------------------------------
# OVERRIDE REBUILD YEAR (Optional)
# POST /planning/api/calendar/override/rebuild-year
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/override/rebuild-year", methods=["POST"])
def api_override_rebuild_year():
    """
    Force a full rebuild of JSON schedules for a given year, including all overrides.
    
    This is useful for maintenance/admin actions or after significant changes.
    
    Request JSON:
    {
        "year": 2025
    }
    
    Response JSON (success):
    {
        "success": true,
        "year": 2025
    }
    """
    try:
        data = get_json()
        year_raw = data.get("year")
        
        if year_raw is None:
            return json_error("year is required")
        
        year = _to_int(year_raw, "year")
        
        # Rebuild all categories for this year
        try:
            from utils.calendar_schedule_builder import write_year_all_categories_json
            
            file_paths = write_year_all_categories_json(year)
            logger.info(
                "Rebuilt all categories for year=%s (%s files)", year, len(file_paths)
            )
        except ImportError:
            logger.warning(
                "Could not import calendar_schedule_builder; rebuild skipped"
            )
            return json_error("JSON builder not available", status=503)
        except Exception as e:
            logger.error("Error rebuilding year=%s: %s", year, e)
            return json_error(f"Rebuild failed: {str(e)}", status=500)
        
        return jsonify(
            {
                "success": True,
                "year": year,
            }
        )
    
    except ValueError as e:
        logger.warning("Validation error in api_override_rebuild_year: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_override_rebuild_year")
        return json_error("Internal server error", status=500)

