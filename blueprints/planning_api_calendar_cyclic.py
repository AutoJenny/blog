"""
Planning Calendar API - Base Cyclic List Management

Provides endpoints for managing base cyclic lists (reorder, add, delete).

This module is WEEK-AGNOSTIC and YEAR-AGNOSTIC. It only manages the base
sequential lists that feed into the JSON builder.

Design constraint: NO week numbers, NO years, NO override logic in this file.
"""

from flask import Blueprint, request, jsonify
from config.database import db_manager
from datetime import datetime
import logging

from utils.calendar_resolver import get_category_config

logger = logging.getLogger(__name__)

bp = Blueprint("planning_api_calendar_cyclic", __name__, url_prefix="/planning")

# Supported categories (must match JSON builder and display API)
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
    return jsonify({"status": "error", "message": message}), status


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


def _normalize_category(category: str) -> tuple[str, str | None]:
    """
    Normalize category for internal use.
    
    Returns:
        (normalized_category, classification)
    
    Examples:
        "profile_product" -> ("profile", "product")
        "weekly_word" -> ("weekly_word", "weekly_word")
        "theme" -> ("theme", None)
    """
    category = category.strip().lower()
    
    # Handle profile categories
    if category in ("profile_product", "profile_surname"):
        profile_type = category.replace("profile_", "")
        return ("profile", profile_type)
    
    # Weekly word/phrase use the category as classification
    if category in ("weekly_word", "weekly_phrase"):
        return (category, category)
    
    # Theme and recipe have no classification
    return (category, None)


def _trigger_json_rebuild(category: str):
    """
    Trigger JSON rebuild for all years after a list change.
    
    Rebuilds all years that have JSON files (typically current year ± 5 years).
    This ensures the display API always has up-to-date schedules.
    
    Args:
        category: Original category name (e.g., "theme", "profile_product")
    """
    try:
        from utils.calendar_schedule_builder import build_year
        from pathlib import Path
        from datetime import datetime
        
        current_year = datetime.now().year
        
        # Determine years to rebuild by checking existing JSON files
        # Look for JSON files in both directory and flat layouts
        base_dir = Path(__file__).resolve().parents[2] / "data" / "calendar" / "schedule"
        
        years_to_rebuild = set()
        
        # Check directory layout: data/calendar/schedule/<category>/<year>.json
        category_dir = base_dir / category
        if category_dir.exists():
            for json_file in category_dir.glob("*.json"):
                try:
                    year = int(json_file.stem)
                    years_to_rebuild.add(year)
                except ValueError:
                    continue
        
        # Check flat layout: data/calendar/schedule/<category>_<year>.json
        for json_file in base_dir.glob(f"{category}_*.json"):
            try:
                # Extract year from filename like "theme_2025.json"
                year_str = json_file.stem.split("_")[-1]
                year = int(year_str)
                years_to_rebuild.add(year)
            except (ValueError, IndexError):
                continue
        
        # If no existing files found, rebuild current year and next 2 years
        if not years_to_rebuild:
            years_to_rebuild = {current_year, current_year + 1, current_year + 2}
        else:
            # Also ensure we rebuild current year and next year even if no files exist
            years_to_rebuild.add(current_year)
            years_to_rebuild.add(current_year + 1)
        
        # Rebuild all years
        for year in sorted(years_to_rebuild):
            try:
                build_year(category, year)
                logger.info(
                    "Rebuilt JSON for category=%s year=%s after list change",
                    category,
                    year,
                )
            except Exception as e:
                logger.error(
                    "Failed to rebuild JSON for category=%s year=%s: %s",
                    category,
                    year,
                    e,
                )
                # Continue with other years even if one fails
    except ImportError:
        logger.warning(
            "Could not import calendar_schedule_builder; JSON rebuild skipped"
        )
    except Exception as e:
        logger.error("Error triggering JSON rebuild: %s", e)
        # Don't fail the list operation if rebuild fails


# ---------------------------------------------------------------------------
# LIST REORDER
# POST /planning/api/calendar/list/reorder
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/list/reorder", methods=["POST"])
def api_list_reorder():
    """
    Reorder an item within its cyclic list, shifting others to keep positions dense 1..N.

    Request JSON:
    {
        "category": "theme" | "recipe" | "profile_product" | "profile_surname" | "weekly_word" | "weekly_phrase",
        "item_id": <int>,
        "new_position": <int>,
        "classification": <optional string>  # only needed for ambiguous categories
    }

    Response JSON (success):
    {
        "status": "ok",
        "category": "theme",
        "item_id": 123,
        "old_position": 3,
        "new_position": 7
    }
    """
    try:
        data = get_json()
        category = data.get("category")
        item_id_raw = data.get("item_id")
        new_pos_raw = data.get("new_position")
        classification = data.get("classification")

        # Validation
        if not category:
            return json_error("category is required")
        if category not in SUPPORTED_CATEGORIES:
            return json_error(
                f"Unknown category: {category}. Supported: {', '.join(SUPPORTED_CATEGORIES)}"
            )
        if item_id_raw is None:
            return json_error("item_id is required")
        if new_pos_raw is None:
            return json_error("new_position is required")

        item_id = _to_int(item_id_raw, "item_id")
        new_pos = _to_int(new_pos_raw, "new_position")

        # Normalize category
        original_category = category
        normalized_category, default_classification = _normalize_category(category)
        if classification is None:
            classification = default_classification

        # Get category config
        cfg = get_category_config(normalized_category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        pos_col = cfg["position_column"]
        extra_filter = cfg["extra_filter"]

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Load current position
                base_sql = f"SELECT {pos_col} AS position FROM {table} WHERE {id_col} = %s"
                params = [item_id]

                if extra_filter:
                    cond, extra_params = extra_filter
                    base_sql += f" AND {cond}"
                    params.extend(extra_params)

                cursor.execute(base_sql, tuple(params))
                row = cursor.fetchone()

                if not row:
                    return json_error("Item not found", status=404)

                old_pos = row["position"]

                # Find max position in this logical list
                max_sql = f"SELECT COALESCE(MAX({pos_col}), 0) AS max_pos FROM {table}"
                max_params = []

                if extra_filter:
                    cond, extra_params = extra_filter
                    max_sql += f" WHERE {cond}"
                    max_params.extend(extra_params)

                cursor.execute(max_sql, tuple(max_params))
                max_row = cursor.fetchone()
                max_pos = max_row["max_pos"] or 0 if max_row else 0

                if max_pos < 1:
                    return json_error("List is empty; cannot reorder", status=400)

                if new_pos < 1 or new_pos > max_pos:
                    return json_error(f"new_position must be between 1 and {max_pos}")

                if new_pos == old_pos:
                    return jsonify(
                        {
                            "status": "ok",
                            "category": original_category,
                            "item_id": item_id,
                            "old_position": old_pos,
                            "new_position": new_pos,
                        }
                    )

                # Two-phase update to avoid unique constraint violations
                # Phase 1: Move all affected items to temporary negative positions
                # Phase 2: Move them to their final positions
                
                if extra_filter:
                    cond, extra_params = extra_filter
                    filter_where = f" AND {cond}"
                    filter_params_base = list(extra_params)
                else:
                    filter_where = ""
                    filter_params_base = []
                
                if new_pos > old_pos:
                    # Moving down: items in (old_pos, new_pos] shift up by 1
                    # Phase 1: Move all affected items (including the one being moved) to temp positions
                    temp_base = -(max_pos + 1000)  # Start from a large negative number
                    
                    # Get all items that need to move
                    sql_get_affected = f"""
                        SELECT {id_col}, {pos_col}
                        FROM {table}
                        WHERE (({pos_col} > %s AND {pos_col} <= %s) OR {id_col} = %s)
                        {filter_where}
                        ORDER BY {pos_col}
                    """
                    params_get = [old_pos, new_pos, item_id] + filter_params_base
                    cursor.execute(sql_get_affected, tuple(params_get))
                    affected_items = cursor.fetchall()
                    
                    # Phase 1: Move all to temporary positions
                    for idx, row in enumerate(affected_items):
                        temp_pos = temp_base - idx
                        affected_id = row[id_col]
                        sql_temp = f"UPDATE {table} SET {pos_col} = %s WHERE {id_col} = %s {filter_where}"
                        params_temp = [temp_pos, affected_id] + filter_params_base
                        cursor.execute(sql_temp, tuple(params_temp))
                    
                    # Phase 2: Move to final positions
                    for row in affected_items:
                        affected_id = row[id_col]
                        affected_old_pos = row[pos_col]
                        
                        if affected_id == item_id:
                            # This is the item being moved - goes to new_pos
                            final_pos = new_pos
                        else:
                            # Other items shift up by 1
                            final_pos = affected_old_pos - 1
                        
                        sql_final = f"UPDATE {table} SET {pos_col} = %s WHERE {id_col} = %s {filter_where}"
                        params_final = [final_pos, affected_id] + filter_params_base
                        cursor.execute(sql_final, tuple(params_final))
                else:
                    # Moving up: items in [new_pos, old_pos) shift down by 1
                    temp_base = -(max_pos + 1000)
                    
                    # Get all items that need to move (in reverse order to avoid conflicts)
                    sql_get_affected = f"""
                        SELECT {id_col}, {pos_col}
                        FROM {table}
                        WHERE (({pos_col} >= %s AND {pos_col} < %s) OR {id_col} = %s)
                        {filter_where}
                        ORDER BY {pos_col} DESC
                    """
                    params_get = [new_pos, old_pos, item_id] + filter_params_base
                    cursor.execute(sql_get_affected, tuple(params_get))
                    affected_items = cursor.fetchall()
                    
                    # Phase 1: Move all to temporary positions
                    for idx, row in enumerate(affected_items):
                        temp_pos = temp_base - idx
                        affected_id = row[id_col]
                        sql_temp = f"UPDATE {table} SET {pos_col} = %s WHERE {id_col} = %s {filter_where}"
                        params_temp = [temp_pos, affected_id] + filter_params_base
                        cursor.execute(sql_temp, tuple(params_temp))
                    
                    # Phase 2: Move to final positions (in reverse order)
                    for row in affected_items:
                        affected_id = row[id_col]
                        affected_old_pos = row[pos_col]
                        
                        if affected_id == item_id:
                            # This is the item being moved - goes to new_pos
                            final_pos = new_pos
                        else:
                            # Other items shift down by 1
                            final_pos = affected_old_pos + 1
                        
                        sql_final = f"UPDATE {table} SET {pos_col} = %s WHERE {id_col} = %s {filter_where}"
                        params_final = [final_pos, affected_id] + filter_params_base
                        cursor.execute(sql_final, tuple(params_final))
                conn.commit()

        # Trigger JSON rebuild
        _trigger_json_rebuild(original_category)

        return jsonify(
            {
                "status": "ok",
                "category": original_category,
                "item_id": item_id,
                "old_position": old_pos,
                "new_position": new_pos,
            }
        )

    except ValueError as e:
        logger.warning("Validation error in api_list_reorder: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_list_reorder")
        return json_error("Internal server error", status=500)


# ---------------------------------------------------------------------------
# LIST ADD
# POST /planning/api/calendar/list/add
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/list/add", methods=["POST"])
def api_list_add():
    """
    Insert a new item into the cyclic list, shifting others as needed.

    Request JSON:
    {
        "category": "...",
        "insert_position": <int or null>,  # null/omitted => append to end
        "classification": <optional string>,
        "data": {
            "theme_title": "...",           # for theme
            "recipe_title": "...",          # for recipe
            "post_id": <int>,               # for profile_product/profile_surname
            "idea_title": "..."             # for weekly_word/weekly_phrase
        }
    }

    Response JSON (success):
    {
        "status": "ok",
        "category": "recipe",
        "item_id": 456,
        "position": 5
    }
    """
    try:
        data = get_json()
        category = data.get("category")
        insert_pos_raw = data.get("insert_position")
        classification = data.get("classification")
        payload = data.get("data") or {}

        # Validation
        if not category:
            return json_error("category is required")
        if category not in SUPPORTED_CATEGORIES:
            return json_error(
                f"Unknown category: {category}. Supported: {', '.join(SUPPORTED_CATEGORIES)}"
            )

        # Normalize category
        original_category = category
        normalized_category, default_classification = _normalize_category(category)
        if classification is None:
            classification = default_classification

        # Strong typing (only if provided)
        insert_pos = None
        if insert_pos_raw is not None:
            insert_pos = _to_int(insert_pos_raw, "insert_position")

        # Get category config
        cfg = get_category_config(normalized_category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        pos_col = cfg["position_column"]
        extra_filter = cfg["extra_filter"]

        # Determine required fields based on category
        required_fields = []
        insert_fields = []
        if original_category == "theme":
            required_fields = ["theme_title"]
            insert_fields = ["theme_title", "theme_description"]
        elif original_category == "recipe":
            required_fields = ["recipe_title"]
            insert_fields = ["recipe_title", "recipe_description"]
        elif original_category in ("profile_product", "profile_surname"):
            required_fields = ["post_id"]
            insert_fields = ["post_id"]
        elif original_category in ("weekly_word", "weekly_phrase"):
            required_fields = ["idea_title"]
            insert_fields = ["idea_title"]

        # Validate required fields
        for field in required_fields:
            if field not in payload:
                return json_error(f"Missing required field: {field}")

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Determine max position
                max_sql = f"SELECT COALESCE(MAX({pos_col}), 0) AS max_pos FROM {table}"
                max_params = []

                if extra_filter:
                    cond, extra_params = extra_filter
                    max_sql += f" WHERE {cond}"
                    max_params.extend(extra_params)

                cursor.execute(max_sql, tuple(max_params))
                max_row = cursor.fetchone()
                max_pos = max_row["max_pos"] or 0 if max_row else 0

                # Determine insert position
                if insert_pos is None:
                    insert_pos = max_pos + 1
                else:
                    if insert_pos < 1 or insert_pos > max_pos + 1:
                        return json_error(
                            f"insert_position must be between 1 and {max_pos + 1}"
                        )

                # Shift existing positions if inserting into the middle
                if insert_pos <= max_pos and max_pos > 0:
                    if extra_filter:
                        cond, extra_params = extra_filter
                        sql_shift = (
                            f"UPDATE {table} "
                            f"SET {pos_col} = {pos_col} + 1 "
                            f"WHERE {pos_col} >= %s AND {cond}"
                        )
                        params_shift = [insert_pos]
                        params_shift.extend(extra_params)
                    else:
                        sql_shift = (
                            f"UPDATE {table} "
                            f"SET {pos_col} = {pos_col} + 1 "
                            f"WHERE {pos_col} >= %s"
                        )
                        params_shift = [insert_pos]

                    cursor.execute(sql_shift, tuple(params_shift))

                # Build insert statement
                columns = [pos_col]
                values = ["%s"]
                params_insert = [insert_pos]

                # Add category-specific fields
                for field in insert_fields:
                    if field in payload:
                        columns.append(field)
                        values.append("%s")
                        params_insert.append(payload[field])

                # Add classification field if needed
                if extra_filter:
                    cond, extra_params = extra_filter
                    # Extract column name from condition (e.g., "profile_type = %s" -> "profile_type")
                    col_name = cond.split("=")[0].strip()
                    columns.append(col_name)
                    values.append("%s")
                    params_insert.append(extra_params[0])

                sql_insert = (
                    f"INSERT INTO {table} ({', '.join(columns)}) "
                    f"VALUES ({', '.join(values)}) "
                    f"RETURNING {id_col} AS item_id"
                )

                cursor.execute(sql_insert, tuple(params_insert))
                row = cursor.fetchone()
                new_item_id = row["item_id"]

                conn.commit()

        # Trigger JSON rebuild
        _trigger_json_rebuild(original_category)

        return jsonify(
            {
                "status": "ok",
                "category": original_category,
                "item_id": new_item_id,
                "position": insert_pos,
            }
        )

    except ValueError as e:
        logger.warning("Validation error in api_list_add: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_list_add")
        return json_error("Internal server error", status=500)


# ---------------------------------------------------------------------------
# LIST DELETE
# POST /planning/api/calendar/list/delete
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/list/delete", methods=["POST"])
def api_list_delete():
    """
    Delete an item from the cyclic list and shift positions above it down by 1.

    Request JSON:
    {
        "category": "...",
        "item_id": <int>,
        "classification": <optional string>
    }

    Response JSON (success):
    {
        "status": "ok",
        "category": "weekly_phrase",
        "item_id": 789,
        "deleted_position": 12
    }
    """
    try:
        data = get_json()
        category = data.get("category")
        item_id_raw = data.get("item_id")
        classification = data.get("classification")

        # Validation
        if not category:
            return json_error("category is required")
        if category not in SUPPORTED_CATEGORIES:
            return json_error(
                f"Unknown category: {category}. Supported: {', '.join(SUPPORTED_CATEGORIES)}"
            )
        if item_id_raw is None:
            return json_error("item_id is required")

        item_id = _to_int(item_id_raw, "item_id")

        # Normalize category
        original_category = category
        normalized_category, default_classification = _normalize_category(category)
        if classification is None:
            classification = default_classification

        # Get category config
        cfg = get_category_config(normalized_category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        pos_col = cfg["position_column"]
        extra_filter = cfg["extra_filter"]

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get current position
                sql_pos = f"SELECT {pos_col} AS position FROM {table} WHERE {id_col} = %s"
                params = [item_id]

                if extra_filter:
                    cond, extra_params = extra_filter
                    sql_pos += f" AND {cond}"
                    params.extend(extra_params)

                cursor.execute(sql_pos, tuple(params))
                row = cursor.fetchone()

                if not row:
                    return json_error("Item not found", status=404)

                old_pos = row["position"]

                # Find max position in this logical list (needed for temp positions)
                max_sql = f"SELECT COALESCE(MAX({pos_col}), 0) AS max_pos FROM {table}"
                max_params = []

                if extra_filter:
                    cond, extra_params = extra_filter
                    max_sql += f" WHERE {cond}"
                    max_params.extend(extra_params)

                cursor.execute(max_sql, tuple(max_params))
                max_row = cursor.fetchone()
                max_pos = max_row["max_pos"] or 0 if max_row else 0

                # Delete the item
                sql_del = f"DELETE FROM {table} WHERE {id_col} = %s"
                params_del = [item_id]

                if extra_filter:
                    cond, extra_params = extra_filter
                    sql_del += f" AND {cond}"
                    params_del.extend(extra_params)

                # Two-phase delete to avoid unique constraint violations
                # Phase 1: Move all items above the deleted one to temporary negative positions
                if extra_filter:
                    cond, extra_params = extra_filter
                    filter_where = f" AND {cond}"
                    filter_params_base = list(extra_params)
                else:
                    filter_where = ""
                    filter_params_base = []
                
                # Get all items that need to shift (those with position > old_pos)
                sql_get_shift = f"""
                    SELECT {id_col}, {pos_col}
                    FROM {table}
                    WHERE {pos_col} > %s {filter_where}
                    ORDER BY {pos_col}
                """
                params_get = [old_pos] + filter_params_base
                cursor.execute(sql_get_shift, tuple(params_get))
                items_to_shift = cursor.fetchall()
                
                # Phase 1: Move items to temporary negative positions
                temp_base = -(max_pos + 1000)
                for idx, row in enumerate(items_to_shift):
                    temp_pos = temp_base - idx
                    shift_id = row[id_col]
                    sql_temp = f"UPDATE {table} SET {pos_col} = %s WHERE {id_col} = %s {filter_where}"
                    params_temp = [temp_pos, shift_id] + filter_params_base
                    cursor.execute(sql_temp, tuple(params_temp))
                
                # Delete the item
                cursor.execute(sql_del, tuple(params_del))
                
                # Phase 2: Move shifted items to their final positions (one less than before)
                for row in items_to_shift:
                    shift_id = row[id_col]
                    original_pos = row[pos_col]
                    final_pos = original_pos - 1
                    sql_final = f"UPDATE {table} SET {pos_col} = %s WHERE {id_col} = %s {filter_where}"
                    params_final = [final_pos, shift_id] + filter_params_base
                    cursor.execute(sql_final, tuple(params_final))
                conn.commit()

        # Trigger JSON rebuild
        _trigger_json_rebuild(original_category)

        return jsonify(
            {
                "status": "ok",
                "category": original_category,
                "item_id": item_id,
                "deleted_position": old_pos,
            }
        )

    except ValueError as e:
        logger.warning("Validation error in api_list_delete: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_list_delete")
        return json_error("Internal server error", status=500)


# ---------------------------------------------------------------------------
# ITEM UPDATE (Content Only)
# POST /planning/api/calendar/item/update
# ---------------------------------------------------------------------------

@bp.route("/api/calendar/item/update", methods=["POST"])
def api_item_update():
    """
    Update content fields of an item (title, description, etc.) without changing position.
    
    Request JSON:
    {
        "category": "theme",
        "item_id": 123,
        "title": "New Title",  // category-specific field
        "description": "...",  // optional
        "classification": "product"  // optional, for profiles
    }
    
    Response JSON (success):
    {
        "status": "ok",
        "category": "theme",
        "item_id": 123
    }
    """
    try:
        data = get_json()
        category = data.get("category")
        item_id_raw = data.get("item_id")
        classification = data.get("classification")
        
        # Validation
        if not category:
            return json_error("category is required")
        if category not in SUPPORTED_CATEGORIES:
            return json_error(
                f"Unknown category: {category}. Supported: {', '.join(SUPPORTED_CATEGORIES)}"
            )
        if item_id_raw is None:
            return json_error("item_id is required")
        
        item_id = _to_int(item_id_raw, "item_id")
        
        # Normalize category
        original_category = category
        normalized_category, default_classification = _normalize_category(category)
        if classification is None:
            classification = default_classification
        
        # Get category config
        cfg = get_category_config(normalized_category, classification)
        table = cfg["table"]
        id_col = cfg["id_column"]
        extra_filter = cfg["extra_filter"]
        
        # Determine updatable fields based on category
        updatable_fields = {}
        if original_category == "theme":
            if "theme_title" in data:
                updatable_fields["theme_title"] = data["theme_title"]
            if "theme_description" in data:
                updatable_fields["theme_description"] = data["theme_description"]
        elif original_category == "recipe":
            if "recipe_title" in data:
                updatable_fields["recipe_title"] = data["recipe_title"]
            if "recipe_description" in data:
                updatable_fields["recipe_description"] = data["recipe_description"]
        elif original_category in ("profile_product", "profile_surname"):
            # Profiles are linked via post_id, so we might update post metadata
            # For now, we don't update profiles here - they're managed via posts
            return json_error("Profile items should be updated via post management", status=400)
        elif original_category in ("weekly_word", "weekly_phrase"):
            if "idea_title" in data:
                updatable_fields["idea_title"] = data["idea_title"]
            if "idea_description" in data:
                updatable_fields["idea_description"] = data["idea_description"]
        
        if not updatable_fields:
            return json_error("No updatable fields provided")
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Build UPDATE statement
                set_clauses = [f"{field} = %s" for field in updatable_fields.keys()]
                set_values = list(updatable_fields.values())
                
                sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {id_col} = %s"
                params = set_values + [item_id]
                
                if extra_filter:
                    cond, extra_params = extra_filter
                    sql += f" AND {cond}"
                    params.extend(extra_params)
                
                cursor.execute(sql, tuple(params))
                
                if cursor.rowcount == 0:
                    return json_error("Item not found", status=404)
                
                conn.commit()
        
        # Trigger JSON rebuild to reflect title/description changes
        _trigger_json_rebuild(original_category)
        
        return jsonify(
            {
                "status": "ok",
                "category": original_category,
                "item_id": item_id,
            }
        )
    
    except ValueError as e:
        logger.warning("Validation error in api_item_update: %s", e)
        return json_error(str(e))
    except Exception as e:
        logger.exception("Error in api_item_update")
        return json_error("Internal server error", status=500)
