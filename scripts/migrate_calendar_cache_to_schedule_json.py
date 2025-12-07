import json
import os
from datetime import datetime, timezone


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SOURCE_CACHE_PATH = os.path.join(DATA_DIR, "calendar_scheduling_cache.json")

# New JSON-centric schedule directory structure
SCHEDULE_BASE_DIR = os.path.join(DATA_DIR, "schedule")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_cache() -> dict:
    with open(SOURCE_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_category_maps(cache: dict) -> dict:
    """
    Transform the existing calendar_scheduling_cache.json structure into
    per-category, per-year week entries that match the new specimen model.

    Output structure:
    {
        "theme": {2025: [ {week, item_id, position, title}, ... ]},
        "recipe": {2025: [ {week, item_id, position, title}, ... ]},
        "weekly_word": {2025: [ {week, id, position, title}, ... ]},
        "weekly_phrase": {2025: [ {week, id, position, title}, ... ]},
        "profile_product": {2025: []},
        "profile_surname": {2025: []},
    }
    """
    result = {
        "theme": {},
        "recipe": {},
        "profile_product": {},
        "profile_surname": {},
        "weekly_word": {},
        "weekly_phrase": {},
    }

    weeks = cache.get("data", {}).get("weeks", [])

    for week_entry in weeks:
        year = week_entry.get("year")
        week = week_entry.get("week")
        schedule_items = week_entry.get("schedule", [])

        if year is None or week is None:
            continue

        # Ensure year buckets exist
        for cat in result.keys():
            result[cat].setdefault(year, [])

        for item in schedule_items:
            item_type = item.get("type")

            if item_type == "theme_selection":
                # Map to theme specimen: {week, item_id, position, title}
                result["theme"][year].append(
                    {
                        "week": week,
                        "item_id": item.get("selected_theme_id") or item.get("theme_id"),
                        "position": item.get("position"),
                        "title": item.get("theme_title"),
                    }
                )
            elif item_type == "recipe":
                # Map to recipe specimen: {week, item_id, position, title}
                result["recipe"][year].append(
                    {
                        "week": week,
                        "item_id": item.get("recipe_id"),
                        "position": item.get("position"),
                        "title": item.get("recipe_title"),
                    }
                )
            elif item_type == "weekly_word":
                # Map to weekly_word specimen: {week, id, position, title}
                # Description is not present in the cache; left out for now.
                result["weekly_word"][year].append(
                    {
                        "week": week,
                        "id": item.get("item_id"),
                        "position": item.get("position"),
                        "title": item.get("title"),
                    }
                )
            elif item_type == "weekly_phrase":
                # Map to weekly_phrase specimen: {week, id, position, title}
                # Description is not present in the cache; left out for now.
                result["weekly_phrase"][year].append(
                    {
                        "week": week,
                        "id": item.get("item_id"),
                        "position": item.get("position"),
                        "title": item.get("title"),
                    }
                )
            else:
                # Other types (e.g. profiles) are not yet present in this cache
                continue

    return result


def write_category_files(category_maps: dict) -> None:
    """
    Write per-category per-year JSON files under data/schedule/{category}/{year}.json
    plus a meta file per year under data/schedule/meta/{year}.json.
    """
    ensure_dir(SCHEDULE_BASE_DIR)

    # Collect all years that appear in any category
    years = set()
    for cat_data in category_maps.values():
        years.update(cat_data.keys())

    generated_at = datetime.now(timezone.utc).isoformat()

    # Per-category, per-year files
    for category, per_year in category_maps.items():
        category_dir = os.path.join(SCHEDULE_BASE_DIR, category)
        ensure_dir(category_dir)

        for year in years:
            entries = per_year.get(year, [])
            # Sort by week for consistency
            entries_sorted = sorted(entries, key=lambda e: e.get("week", 0))

            target_path = os.path.join(category_dir, f"{year}.json")
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(entries_sorted, f, ensure_ascii=False, indent=2)

    # Meta files per year
    meta_dir = os.path.join(SCHEDULE_BASE_DIR, "meta")
    ensure_dir(meta_dir)

    categories_list = list(category_maps.keys())

    for year in years:
        meta = {
            "year": year,
            "categories": categories_list,
            "generated_at": generated_at,
            "notes": "Auto-generated from calendar_scheduling_cache.json by migrate_calendar_cache_to_schedule_json.py",
        }
        meta_path = os.path.join(meta_dir, f"{year}.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)


def main() -> None:
    if not os.path.exists(SOURCE_CACHE_PATH):
        raise SystemExit(f"Source cache not found: {SOURCE_CACHE_PATH}")

    cache = load_cache()
    category_maps = build_category_maps(cache)
    write_category_files(category_maps)


if __name__ == "__main__":
    main()


