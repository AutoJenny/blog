import sys
from pathlib import Path
import logging
import re
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TartanNameNormalizer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        
    def normalize_clan_name(self, name):
        """
        Normalize clan tartan names to extract base_name and suffix.
        
        Examples:
        - "Aberdeen Football Club #2" -> ("Aberdeen Football Club", "#2")
        - "Aberdeen Football Club" -> ("Aberdeen Football Club", "0")
        - "Anderson Arisaid #2" -> ("Anderson Arisaid", "#2")
        - "Black #2; Polyester (Marton Mills)" -> ("Black", "#2")
        - "Bowhill Check Brown #3" -> ("Bowhill Check", "Brown #3")
        - "Bowhill Check Brown" -> ("Bowhill Check", "Brown")
        """
        if not name:
            return None, "0"
            
        # Clean up the name first
        clean_name = name.strip()
        
        # Check for color suffixes first (before #number patterns)
        color_suffix = self.extract_color_suffix(clean_name)
        if color_suffix:
            base_name = clean_name.replace(color_suffix, '').strip()
            return base_name, color_suffix
        
        # Pattern to match #number suffix (most common)
        pattern = r'^(.+?)\s*#(\d+)(.*)$'
        match = re.match(pattern, clean_name)
        
        if match:
            base_name = match.group(1).strip()
            suffix_num = match.group(2)
            trailing_text = match.group(3).strip()
            # Combine the #number with any trailing text
            full_suffix = f"#{suffix_num}{trailing_text}" if trailing_text else f"#{suffix_num}"
            return base_name, full_suffix
        
        # Check for other patterns like "; Polyester" etc.
        # Pattern for names ending with semicolon and additional info
        pattern = r'^(.+?)\s*;\s*(.+)$'
        match = re.match(pattern, clean_name)
        if match:
            # Check if the part before semicolon has a suffix
            main_part = match.group(1).strip()
            base_name, suffix = self.normalize_clan_name(main_part)
            if suffix != "0":
                return base_name, suffix
        
        # No suffix found, treat as base name with suffix "0"
        return clean_name, "0"
    
    def extract_color_suffix(self, name):
        """
        Extract color names that appear as suffixes (not first words or hyphenated surnames).
        Handles compound suffixes like "Brown #2".
        
        Examples:
        - "Bowhill Check Brown" -> "Brown" (color suffix)
        - "Bowhill Check Brown #2" -> "Brown #2" (compound color suffix)
        - "Bowhill Check Green" -> "Green" (color suffix)  
        - "Brown Check" -> None (Brown is first word)
        - "Jones-Brown" -> None (Brown is part of hyphenated surname)
        - "MacDonald Brown" -> "Brown" (Brown is surname, but could be color)
        """
        # Common color names
        colors = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'brown', 
            'black', 'white', 'grey', 'gray', 'gold', 'silver', 'beige', 'tan',
            'maroon', 'navy', 'teal', 'cyan', 'magenta', 'lime', 'olive', 'coral',
            'crimson', 'scarlet', 'burgundy', 'indigo', 'violet', 'turquoise'
        ]
        
        # Split name into words
        words = name.strip().split()
        if len(words) < 2:
            return None  # Need at least 2 words to have a suffix
        
        # Look for colors in the words (not just the last word)
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in colors:
                # Check if it's not the first word and not a hyphenated surname
                if i > 0 and '-' not in word:
                    # Check if this color word is followed by #number pattern
                    color_word = word  # Original case
                    
                    # Simple check: if the color word is followed by #number in the original string
                    color_pattern = rf'{re.escape(color_word)}\s*#(\d+)(.*)$'
                    match = re.search(color_pattern, name)
                    if match:
                        # Found compound suffix like "Brown #2"
                        number = match.group(1)
                        trailing = match.group(2).strip()
                        full_suffix = f"{color_word} #{number}{trailing}" if trailing else f"{color_word} #{number}"
                        return full_suffix
                    else:
                        # Check if this is the last meaningful word (not followed by #number)
                        # If there are more words after this color, it might not be a suffix
                        remaining_words = words[i+1:]
                        if not remaining_words or all(w.startswith('#') for w in remaining_words):
                            return color_word  # Return original case
        
        return None
    
    def normalize_register_name(self, name):
        """
        Normalize register tartan names to extract base_name and suffix.
        
        Examples:
        - "Aberdeen Football Club (1990)" -> ("Aberdeen Football Club", "(1990)")
        - "Aberdeen Football Club" -> ("Aberdeen Football Club", "0")
        - "Anderson Dress 2001" -> ("Anderson Dress", "2001")
        - "Allen (Personal)" -> ("Allen", "(Personal)")
        - "Bank of Scotland (1995)" -> ("Bank of Scotland", "(1995)")
        """
        if not name:
            return None, "0"
            
        clean_name = name.strip()
        
        # Pattern to match year in parentheses (1900-2099)
        pattern = r'^(.+?)\s*\((\d{4})\)$'
        match = re.match(pattern, clean_name)
        
        if match:
            base_name = match.group(1).strip()
            year = match.group(2)
            if 1900 <= int(year) <= 2099:  # Reasonable year range
                return base_name, f"({year})"
        
        # Pattern to match year suffix without parentheses (1900-2099)
        pattern = r'^(.+?)\s+(\d{4})$'
        match = re.match(pattern, clean_name)
        
        if match:
            base_name = match.group(1).strip()
            year = match.group(2)
            if 1900 <= int(year) <= 2099:  # Reasonable year range
                return base_name, year
        
        # Pattern to match other parenthetical suffixes
        pattern = r'^(.+?)\s*\(([^)]+)\)$'
        match = re.match(pattern, clean_name)
        if match:
            base_name = match.group(1).strip()
            suffix = match.group(2).strip()
            return base_name, f"({suffix})"
        
        # No suffix found, treat as base name with suffix "0"
        return clean_name, "0"
    
    def add_normalization_fields(self):
        """Add base_name and suffix fields to both tables"""
        try:
            with db_manager.get_cursor() as cursor:
                # Add fields to tartan_designs_clan
                logger.info("Adding normalization fields to tartan_designs_clan...")
                cursor.execute('''
                    ALTER TABLE tartan_designs_clan 
                    ADD COLUMN IF NOT EXISTS base_name VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS suffix VARCHAR(50) DEFAULT '0'
                ''')
                
                # Add fields to tartan_designs_register
                logger.info("Adding normalization fields to tartan_designs_register...")
                cursor.execute('''
                    ALTER TABLE tartan_designs_register 
                    ADD COLUMN IF NOT EXISTS base_name VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS suffix VARCHAR(50) DEFAULT '0'
                ''')
                
                logger.info("✅ Normalization fields added successfully")
                
        except Exception as e:
            logger.error(f"Error adding normalization fields: {e}")
            raise
    
    def populate_clan_normalization(self):
        """Populate base_name and suffix fields for tartan_designs_clan"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get all clan records
                cursor.execute('SELECT id, name FROM tartan_designs_clan ORDER BY id')
                records = cursor.fetchall()
                
                logger.info(f"Processing {len(records)} clan records...")
                
                updated_count = 0
                for record in records:
                    base_name, suffix = self.normalize_clan_name(record['name'])
                    
                    if not self.dry_run:
                        cursor.execute('''
                            UPDATE tartan_designs_clan 
                            SET base_name = %s, suffix = %s 
                            WHERE id = %s
                        ''', (base_name, str(suffix), record['id']))
                    
                    updated_count += 1
                    
                    if updated_count % 1000 == 0:
                        logger.info(f"Processed {updated_count}/{len(records)} clan records...")
                
                logger.info(f"✅ Processed {updated_count} clan records")
                
        except Exception as e:
            logger.error(f"Error populating clan normalization: {e}")
            raise
    
    def populate_register_normalization(self):
        """Populate base_name and suffix fields for tartan_designs_register"""
        try:
            with db_manager.get_cursor() as cursor:
                # Get all register records
                cursor.execute('SELECT id, tartan_name FROM tartan_designs_register ORDER BY id')
                records = cursor.fetchall()
                
                logger.info(f"Processing {len(records)} register records...")
                
                updated_count = 0
                for record in records:
                    base_name, suffix = self.normalize_register_name(record['tartan_name'])
                    
                    if not self.dry_run:
                        cursor.execute('''
                            UPDATE tartan_designs_register 
                            SET base_name = %s, suffix = %s 
                            WHERE id = %s
                        ''', (base_name, str(suffix), record['id']))
                    
                    updated_count += 1
                    
                    if updated_count % 1000 == 0:
                        logger.info(f"Processed {updated_count}/{len(records)} register records...")
                
                logger.info(f"✅ Processed {updated_count} register records")
                
        except Exception as e:
            logger.error(f"Error populating register normalization: {e}")
            raise
    
    def analyze_normalization_results(self):
        """Analyze the normalization results"""
        try:
            with db_manager.get_cursor() as cursor:
                # Analyze clan table
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN suffix != '0' THEN 1 END) as with_suffix,
                        COUNT(CASE WHEN suffix = '0' THEN 1 END) as no_suffix
                    FROM tartan_designs_clan
                ''')
                clan_stats = cursor.fetchone()
                
                # Analyze register table
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN suffix != '0' THEN 1 END) as with_suffix,
                        COUNT(CASE WHEN suffix = '0' THEN 1 END) as no_suffix
                    FROM tartan_designs_register
                ''')
                register_stats = cursor.fetchone()
                
                logger.info("NORMALIZATION ANALYSIS:")
                logger.info(f"CLAN TABLE:")
                logger.info(f"  Total records: {clan_stats['total']}")
                logger.info(f"  With suffix: {clan_stats['with_suffix']}")
                logger.info(f"  No suffix: {clan_stats['no_suffix']}")
                
                logger.info(f"REGISTER TABLE:")
                logger.info(f"  Total records: {register_stats['total']}")
                logger.info(f"  With suffix: {register_stats['with_suffix']}")
                logger.info(f"  No suffix: {register_stats['no_suffix']}")
                
                # Show some examples
                logger.info("\nCLAN EXAMPLES:")
                cursor.execute('''
                    SELECT name, base_name, suffix 
                    FROM tartan_designs_clan 
                    WHERE suffix != '0' 
                    ORDER BY suffix DESC 
                    LIMIT 10
                ''')
                clan_examples = cursor.fetchall()
                for example in clan_examples:
                    logger.info(f"  '{example['name']}' -> '{example['base_name']}' (suffix: {example['suffix']})")
                
                logger.info("\nREGISTER EXAMPLES:")
                cursor.execute('''
                    SELECT tartan_name, base_name, suffix 
                    FROM tartan_designs_register 
                    WHERE suffix != '0' 
                    ORDER BY suffix DESC 
                    LIMIT 10
                ''')
                register_examples = cursor.fetchall()
                for example in register_examples:
                    logger.info(f"  '{example['tartan_name']}' -> '{example['base_name']}' (suffix: {example['suffix']})")
                
        except Exception as e:
            logger.error(f"Error analyzing normalization results: {e}")
            raise
    
    def run_full_normalization(self):
        """Run the complete normalization process"""
        logger.info("Starting tartan name normalization...")
        
        if not self.dry_run:
            logger.info("Running in LIVE mode - database will be updated")
        else:
            logger.info("Running in DRY RUN mode - no database changes will be made")
        
        try:
            # Step 1: Add fields
            self.add_normalization_fields()
            
            # Step 2: Populate clan table
            self.populate_clan_normalization()
            
            # Step 3: Populate register table
            self.populate_register_normalization()
            
            # Step 4: Analyze results
            self.analyze_normalization_results()
            
            logger.info("✅ Normalization complete!")
            
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize tartan names for better matching")
    parser.add_argument('--live', action='store_true', help='Run in live mode (make database changes). Default is dry run.')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze existing normalization data')
    args = parser.parse_args()

    normalizer = TartanNameNormalizer(dry_run=not args.live)
    
    if args.analyze_only:
        normalizer.analyze_normalization_results()
    else:
        normalizer.run_full_normalization()
