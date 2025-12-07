#!/usr/bin/env python3
# c4_json_builder.py
# Utility: JSON Builder CLI for Calendar Scheduling System

import sys
import os
import argparse
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.calendar_schedule_builder import build_year, build_all_categories, CATEGORIES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build calendar schedule JSON files from database"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        help="ISO year to build (e.g., 2025). Required unless using --start-year/--end-year",
    )
    
    parser.add_argument(
        "--category",
        type=str,
        help=f"Single category to build. Supported: {', '.join(CATEGORIES)}",
    )
    
    parser.add_argument(
        "--start-year",
        type=int,
        help="Start year for range build (requires --end-year)",
    )
    
    parser.add_argument(
        "--end-year",
        type=int,
        help="End year for range build (requires --start-year)",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.start_year and args.end_year:
        if args.start_year > args.end_year:
            print("✗ Error: --start-year must be <= --end-year")
            return 1
        years = list(range(args.start_year, args.end_year + 1))
    elif args.year:
        years = [args.year]
    else:
        print("✗ Error: Must provide either --year or both --start-year and --end-year")
        return 1
    
    # Validate category if provided
    if args.category and args.category not in CATEGORIES:
        print(f"✗ Unknown category: {args.category}")
        print(f"  Supported categories: {', '.join(CATEGORIES)}")
        return 1
    
    try:
        for year in years:
            logger.info("Building schedules for year %s...", year)
            
            if args.category:
                # Build single category
                file_path = build_year(args.category, year)
                print(f"✓ Built {args.category}/{year}.json → {file_path}")
            else:
                # Build all categories
                paths = build_all_categories(year)
                print(f"✓ Built all categories for {year} ({len(paths)} files)")
                for category, path in paths.items():
                    print(f"  → {category}/{year}.json")
        
        print("\n✓ Done.")
        return 0
    except Exception as e:
        logger.exception("Error building schedules")
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
