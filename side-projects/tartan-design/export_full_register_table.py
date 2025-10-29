import sys
from pathlib import Path
import logging
import csv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_full_register_table_to_csv(output_filepath):
    """
    Exports ALL fields from tartan_designs_register table to a CSV file.
    """
    try:
        with db_manager.get_cursor() as cursor:
            # Get all column names
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'tartan_designs_register' 
                ORDER BY ordinal_position
            """)
            columns = [row['column_name'] for row in cursor.fetchall()]
            
            # Get all records
            cursor.execute("SELECT * FROM tartan_designs_register ORDER BY id")
            records = cursor.fetchall()

        if not records:
            logger.info("No records found in tartan_designs_register to export.")
            return

        with open(output_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)

            writer.writeheader()
            for record in records:
                writer.writerow(record)

        logger.info(f"Found {len(records)} records in tartan_designs_register")
        logger.info(f"CSV file created: {output_filepath}")
        logger.info(f"Records written: {len(records)}")
        logger.info(f"Columns exported: {', '.join(columns)}")

    except Exception as e:
        logger.error(f"Error exporting full register table to CSV: {e}")

if __name__ == "__main__":
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filepath = output_dir / "tartan_designs_register_full.csv"
    export_full_register_table_to_csv(output_filepath)

