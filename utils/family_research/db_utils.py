"""
Database utilities for family research.
"""

from pathlib import Path
from typing import Dict, Optional
import json

from config.database import db_manager


def get_family_context(family_id: Optional[int] = None, family_name: Optional[str] = None) -> Optional[Dict]:
    """Get existing family data from database."""
    if not family_id and not family_name:
        return None
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            if family_id:
                cur.execute("SELECT * FROM families WHERE id = %s", (family_id,))
            else:
                cur.execute("SELECT * FROM families WHERE name = %s", (family_name,))
            
            family = cur.fetchone()
            if not family:
                return None
            
            return {'family': dict(family)}


def load_template() -> Dict:
    """Load JSON template from file."""
    template_path = Path(__file__).parent.parent.parent / 'data' / 'research_data_template.json'
    with open(template_path, 'r') as f:
        return json.load(f)


