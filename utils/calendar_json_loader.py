"""calendar_json_loader.py

Helper utilities for loading per-category, per-year calendar schedule JSON.

This module is intentionally self-contained and filesystem-only:
- It does NOT touch the database.
- It only reads JSON files from the configured schedule directory.
- On any error (missing file, malformed JSON, invalid structure) it degrades
  gracefully by returning an empty mapping.

Supported JSON layout patterns
------------------------------
We support BOTH of the following on-disk layouts, to make migration easier:

1) Directory-per-category layout (recommended going forward):
    data/calendar/schedule/<category>/<year>.json
    e.g. data/calendar/schedule/theme/2025.json

2) Flat files with category_year pattern:
    data/calendar/schedule/<category>_<year>.json
    e.g. data/calendar/schedule/theme_2025.json

The loader will try the directory layout first, then the flat layout.

JSON schema (per file)
----------------------
Each JSON file MUST be a list of objects, one per week:

    [
      {
        "week": 1,
        "item_id": 101,
        "position": 1,
        "title": "Theme 1"
      },
      ...
    ]

The loader converts this into a mapping:

    {
      1: { ... },   # week 1 entry
      2: { ... },   # week 2 entry
      ...
    }

Any entry missing a usable 'week' integer is ignored.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base directory resolution
# ---------------------------------------------------------------------------

def get_schedule_base_dir() -> Path:
    """Return the base directory for schedule JSON files.

    Resolution order:
    1. Environment variable CALENDAR_SCHEDULE_BASE_DIR (if set)
    2. Project-root-relative: <project_root>/data/calendar/schedule

    Where project_root is assumed to be two levels up from this file:
        utils/calendar_json_loader.py -> project_root/
    """
    # 1) Environment override
    env_path = os.getenv("CALENDAR_SCHEDULE_BASE_DIR")
    if env_path:
        base = Path(env_path).expanduser().resolve()
        if base.is_dir():
            return base
        logger.warning(
            "CALENDAR_SCHEDULE_BASE_DIR=%s does not exist or is not a directory; "
            "falling back to default path.",
            env_path,
        )

    # 2) Default project-root-relative path
    # This assumes the module lives under <project_root>/utils/
    project_root = Path(__file__).resolve().parents[1]
    default_dir = project_root / "data" / "calendar" / "schedule"
    return default_dir


# ---------------------------------------------------------------------------
# Low-level JSON loader
# ---------------------------------------------------------------------------

def _safe_load_json(path: Path) -> List[Dict[str, Any]]:
    """Safely load a JSON file and return it as a list of dicts.

    Supports two formats:
    1. Array format: [{week: 1, item_id: ..., ...}, ...]
    2. Object format: {category: "...", year: ..., weeks: {"1": {...}, ...}}
    
    - If the file does not exist: returns [].
    - If the JSON is malformed: logs a warning and returns [].
    """
    if not path.exists():
        logger.info("Schedule JSON not found at %s", path)
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # broad catch is intentional: we never want to crash
        logger.warning("Failed to load JSON from %s: %s", path, exc)
        return []

    # Handle array format: [{week: 1, ...}, ...]
    if isinstance(data, list):
        cleaned: List[Dict[str, Any]] = []
        for idx, entry in enumerate(data):
            if isinstance(entry, dict):
                cleaned.append(entry)
            else:
                logger.debug(
                    "Ignoring non-dict entry at index %d in %s: %r", idx, path, entry
                )
        return cleaned
    
    # Handle object format: {category: "...", year: ..., weeks: {"1": {...}, ...}}
    if isinstance(data, dict) and "weeks" in data:
        weeks_dict = data["weeks"]
        if isinstance(weeks_dict, dict):
            # Convert weeks dict to array format
            result: List[Dict[str, Any]] = []
            for week_str, entry in weeks_dict.items():
                try:
                    week_num = int(week_str)
                    entry_copy = dict(entry)
                    entry_copy["week"] = week_num
                    # Map "id" to "item_id" for consistency
                    if "id" in entry_copy and "item_id" not in entry_copy:
                        entry_copy["item_id"] = entry_copy["id"]
                    result.append(entry_copy)
                except (ValueError, TypeError):
                    logger.debug("Invalid week key '%s' in %s", week_str, path)
            return result
    
    logger.warning("Schedule JSON at %s has unexpected format (not list or object with weeks); ignoring.", path)
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_category_year(category: str, year: int) -> Dict[int, Dict[str, Any]]:
    """Load schedule JSON for a single (category, year).

    Returns:
        A dict mapping week_number -> entry_dict, e.g.:

            {
              1: {"week": 1, "item_id": 101, "position": 1, "title": "..."},
              2: {...},
              ...
            }

    Behaviour:
    - Tries directory layout first:  <base>/<category>/<year>.json
    - Then flat layout:              <base>/<category>_<year>.json
    - On any error or missing file, returns {}.
    - Entries without a valid 'week' integer (1–53) are ignored.
    - If multiple entries claim the same week, the last one in the file wins.
    """
    category = (category or "").strip().lower()
    if not category:
        logger.error("load_category_year called with empty category.")
        return {}

    base_dir = get_schedule_base_dir()

    # 1) Directory-per-category layout
    path_dir_layout = base_dir / category / f"{year}.json"

    # 2) Flat layout
    path_flat_layout = base_dir / f"{category}_{year}.json"

    # Choose the first that exists; otherwise, we still pass the first to _safe_load_json
    if path_dir_layout.exists():
        chosen = path_dir_layout
    else:
        chosen = path_flat_layout

    raw_entries = _safe_load_json(chosen)
    if not raw_entries:
        return {}

    by_week: Dict[int, Dict[str, Any]] = {}
    for idx, entry in enumerate(raw_entries):
        week = entry.get("week")
        if not isinstance(week, int):
            # Try to coerce from string
            try:
                week = int(str(week))
            except Exception:
                week = None

        if week is None or week < 1 or week > 53:
            logger.debug(
                "Ignoring entry with invalid week=%r at index %d in %s",
                entry.get("week"),
                idx,
                chosen,
            )
            continue

        # Copy to avoid accidental mutations of the original list
        by_week[week] = dict(entry)

    return by_week


def load_categories_for_year(
    year: int, categories: list[str]
) -> Dict[str, Dict[int, Dict[str, Any]]]:
    """Load multiple categories for a given year.

    Returns:
        {
          "theme": { 1: {...}, 2: {...}, ... },
          "recipe": { ... },
          ...
        }

    Any category that fails to load yields an empty dict for that key.
    """
    result: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for category in categories:
        try:
            result[category] = load_category_year(category, year)
        except Exception as exc:
            logger.error(
                "Error loading schedule JSON for category=%s year=%s: %s",
                category,
                year,
                exc,
            )
            result[category] = {}
    return result
