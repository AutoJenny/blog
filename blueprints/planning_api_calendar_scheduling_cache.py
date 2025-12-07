# c2_display_api.py
# Backend Display API — JSON‑backed, range‑based

import os
import json
from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify
import logging

# JSON loader (expects calendar_json_loader.py)
from utils.calendar_json_loader import load_category_year

logger = logging.getLogger(__name__)

bp = Blueprint("planning_api_calendar_scheduling_cache", __name__, url_prefix="/planning")

CATEGORIES = [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase",
]


def iso_year_week(d):
    """Get ISO year and week from a date."""
    iso = d.isocalendar()
    return iso[0], iso[1]


def expand_range(start_year, start_week, weeks):
    """Expand a (start_year, start_week, weeks) into a list of (year, week) tuples."""
    year = start_year
    week = start_week
    out = []
    for _ in range(weeks):
        out.append((year, week))
        week += 1
        if week > 52:
            week = 1
            year += 1
    return out


def build_schedule_item(category: str, entry: dict) -> dict:
    """Convert a raw JSON entry into the structure expected by the frontend."""
    if not entry:
        return None
    
    cat = category.lower()
    
    # Common fields
    item_id = entry.get("item_id") or entry.get("id")
    position = entry.get("position")
    title = entry.get("title")
    
    if cat == "theme":
        result = {
            "type": "theme_selection",
            "theme_id": item_id,
            "selected_theme_id": item_id,
            "theme_title": title,
            "position": position,
        }
        # Include description if available
        description = entry.get("description")
        if description:
            result["theme_description"] = description
        return result
    
    if cat == "recipe":
        return {
            "type": "recipe",
            "recipe_id": item_id,
            "recipe_title": title,
            "position": position,
        }
    
    if cat == "profile_product":
        result = {
            "type": "post",
            "item_type": "profile",
            "profile_type": "product",
            "post_id": item_id,
            "position": position,
        }
        # Include title if available
        if title:
            result["post_title"] = title
        return result
    
    if cat == "profile_surname":
        result = {
            "type": "post",
            "item_type": "profile",
            "profile_type": "surname",
            "post_id": item_id,
            "position": position,
        }
        # Include title if available
        if title:
            result["post_title"] = title
        return result
    
    if cat == "weekly_word":
        result = {
            "type": "weekly_word",
            "item_id": item_id,
            "title": title,
            "position": position,
        }
        # Include description if available
        description = entry.get("description")
        if description:
            result["description"] = description
        return result
    
    if cat == "weekly_phrase":
        result = {
            "type": "weekly_phrase",
            "item_id": item_id,
            "title": title,
            "position": position,
        }
        # Include description if available
        description = entry.get("description")
        if description:
            result["description"] = description
        return result
    
    return None


@bp.route("/api/calendar/scheduling/all", methods=["GET"])
def scheduling_all():
    """Return scheduling data for a range of weeks, reading from JSON files."""
    try:
        # 1. Current ISO week
        today = datetime.utcnow().date()
        cur_year, cur_week = iso_year_week(today)

        # 2. Parse params
        try:
            start_year = int(request.args.get("start_year", cur_year))
            start_week = int(request.args.get("start_week", cur_week))
            weeks = int(request.args.get("weeks", 52))
        except (ValueError, TypeError):
            start_year, start_week, weeks = cur_year, cur_week, 52

        # Validate weeks parameter
        if weeks < 1:
            weeks = 1
        if weeks > 260:  # Reasonable max (5 years)
            weeks = 260

        # 3. Build week list
        range_weeks = expand_range(start_year, start_week, weeks)

        # 4. Collect all needed years
        years_needed = sorted(set(y for y, _ in range_weeks))

        # 5. Load JSON for all categories × years
        data = {}
        for cat in CATEGORIES:
            data[cat] = {}
            for y in years_needed:
                data[cat][y] = load_category_year(cat, y)

        # 6. Merge structure
        merged = []
        for (y, w) in range_weeks:
            row = {"year": y, "week": w, "schedule": []}
            week_items = []

            for cat in CATEGORIES:
                entry = data[cat].get(y, {}).get(w)
                if entry:
                    item = build_schedule_item(cat, entry)
                    if item:
                        week_items.append(item)

            row["schedule"] = week_items
            merged.append(row)

        # 7. Return format
        return jsonify({
            "success": True,
            "data": {
                "current_year": cur_year,
                "current_week": cur_week,
                "range_start_year": start_year,
                "range_start_week": start_week,
                "range_weeks": weeks,
                "weeks": merged,
            }
        })

    except Exception as e:
        logger.exception("Error in scheduling_all")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# Stub for backward compatibility
def invalidate_scheduling_cache():
    """Stub function for backward compatibility with other blueprints."""
    logger.debug("invalidate_scheduling_cache called (no-op in JSON-backed system)")
