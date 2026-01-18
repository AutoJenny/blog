# c2_display_api.py
# Backend Display API — JSON‑backed, range‑based

import os
import json
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from flask import Blueprint, request, jsonify
import logging

# JSON loader (expects calendar_json_loader.py)
from utils.calendar_json_loader import load_category_year
from utils.publication_status_resolver import resolve_post_for_calendar_item

logger = logging.getLogger(__name__)

bp = Blueprint("planning_api_calendar_scheduling_cache", __name__, url_prefix="/planning")

CATEGORIES = [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase",
    "weekly_insult",
    "product",  # Product posts from posting_queue
]


def iso_year_week(d):
    """Get ISO year and week from a date."""
    iso = d.isocalendar()
    return iso[0], iso[1]


def _get_week_start_date(year, week):
    """Get the Monday (start date) of an ISO week."""
    jan4 = date(year, 1, 4)
    jan4_day = (jan4.isoweekday() + 6) % 7  # Monday = 0
    week_start = date(year, 1, 4) + timedelta(days=(week - 1) * 7 - jan4_day)
    return week_start


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
    
    if cat == "weekly_insult":
        result = {
            "type": "weekly_insult",
            "item_id": item_id,
            "title": title,
            "position": position,
        }
        # Include description if available
        description = entry.get("description")
        if description:
            result["description"] = description
        return result
    
    if cat == "product":
        result = {
            "type": "product",
            "item_id": item_id,
            "product_id": entry.get("product_id") or item_id,
            "posting_queue_id": entry.get("posting_queue_id") or item_id,
            "title": title,
            "position": position,
        }
        # Include scheduled date/time if available
        if entry.get("scheduled_date"):
            result["scheduled_date"] = str(entry["scheduled_date"])
        if entry.get("scheduled_time"):
            result["scheduled_time"] = str(entry["scheduled_time"])
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

        # 5. Load JSON for all categories × years (except product which uses DB)
        data = {}
        for cat in CATEGORIES:
            data[cat] = {}
            if cat == "product":
                # Product posts come from posting_queue, not JSON files
                continue
            for y in years_needed:
                data[cat][y] = load_category_year(cat, y)

        # 5.5. Load product posts from posting_queue (date-based, not JSON)
        product_posts_by_week = {}
        try:
            from config.database import db_manager
            # Get date range for the week range
            if range_weeks:
                first_week = range_weeks[0]
                last_week = range_weeks[-1]
                # Calculate date range: first week Monday to last week Sunday
                first_date = _get_week_start_date(first_week[0], first_week[1])
                last_week_start = _get_week_start_date(last_week[0], last_week[1])
                last_date = last_week_start + timedelta(days=6)  # Sunday of last week
                
                with db_manager.get_cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            pq.id as posting_queue_id,
                            pq.product_id,
                            pq.scheduled_date,
                            pq.scheduled_time,
                            pq.status,
                            cp.name as product_name,
                            cp.sku
                        FROM posting_queue pq
                        LEFT JOIN clan_products cp ON pq.product_id = cp.id
                        WHERE pq.content_type = 'product'
                          AND pq.scheduled_date >= %s
                          AND pq.scheduled_date <= %s
                          AND pq.scheduled_timestamp IS NOT NULL
                        ORDER BY pq.scheduled_date, pq.scheduled_time
                    """, (first_date, last_date))
                    product_posts = cursor.fetchall()
                    
                    # Group by week
                    for post in product_posts:
                        if post['scheduled_date']:
                            year, week = iso_year_week(post['scheduled_date'])
                            week_key = (year, week)
                            if week_key not in product_posts_by_week:
                                product_posts_by_week[week_key] = []
                            product_posts_by_week[week_key].append({
                                "item_id": post['product_id'],
                                "posting_queue_id": post['posting_queue_id'],
                                "product_id": post['product_id'],
                                "title": post['product_name'] or f"Product {post['product_id']}",
                                "scheduled_date": post['scheduled_date'],
                                "scheduled_time": post['scheduled_time'],
                                "status": post['status'],
                                "position": len(product_posts_by_week[week_key]) + 1
                            })
        except Exception as e:
            logger.error(f"Error loading product posts: {e}")
            import traceback
            logger.error(traceback.format_exc())
            product_posts_by_week = {}

        # 6. Merge structure
        merged = []
        for (y, w) in range_weeks:
            row = {"year": y, "week": w, "schedule": []}
            week_items = []

            # Process JSON-based categories
            for cat in CATEGORIES:
                if cat == "product":
                    continue  # Handle separately below
                    
                entry = data[cat].get(y, {}).get(w)
                if not entry:
                    continue

                item = build_schedule_item(cat, entry)
                if not item:
                    continue

                # Enrich with post linkage/status via central resolver (ID-only).
                category_for_resolver = cat
                if category_for_resolver in ("profile_product", "profile_surname"):
                    # Profiles use post.id as their schedule ID.
                    item_id = entry.get("id") or entry.get("item_id")
                elif category_for_resolver in ("theme", "recipe"):
                    item_id = entry.get("id") or entry.get("item_id")
                else:
                    item_id = None  # Weekly content currently has no post linkage

                if item_id:
                    status_info = resolve_post_for_calendar_item(
                        category_for_resolver, item_id, year=y, week=w
                    )
                    item["post_id"] = status_info.get("post_id")
                    item["post_exists"] = bool(status_info.get("exists"))
                    item["post_status"] = status_info.get("status")

                week_items.append(item)
            
            # Add product posts for this week
            week_key = (y, w)
            if week_key in product_posts_by_week:
                for product_entry in product_posts_by_week[week_key]:
                    item = build_schedule_item("product", product_entry)
                    if item:
                        # Product posts use posting_queue.id for status resolution
                        posting_queue_id = product_entry.get("posting_queue_id")
                        if posting_queue_id:
                            # Check if there's a linked post (product posts might not have posts yet)
                            item["posting_queue_id"] = posting_queue_id
                            item["post_exists"] = False  # Product posts are social posts, not blog posts
                            item["post_status"] = product_entry.get("status", "ready")
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
