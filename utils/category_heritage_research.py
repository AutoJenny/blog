#!/usr/bin/env python3
"""
Category Heritage Research

Researches historical and cultural context for categories using:
1. LLM analysis of aggregated product data
2. Web research to validate and enhance
3. Category hierarchy context
"""

import logging
import json
from typing import Dict, Optional, List
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class CategoryHeritageResearcher:
    """Researches category heritage and cultural context"""
    
    def __init__(self, db_connection, llm_service=None):
        """
        Initialize researcher.
        
        Args:
            db_connection: Database connection
            llm_service: LLM service instance (optional, will create if not provided)
        """
        self.db = db_connection
        
        # Initialize LLM service if not provided
        if llm_service is None:
            try:
                from blueprints.llm_actions import LLMService
                self.llm_service = LLMService()
            except ImportError:
                logger.warning("LLM service not available, heritage research will be limited")
                self.llm_service = None
        else:
            self.llm_service = llm_service
    
    def get_category_path(self, category_id: int) -> List[str]:
        """
        Get category hierarchy path (e.g., ["Homeware", "Plaques", "Clan Crest Plaques"]).
        
        Args:
            category_id: Category ID
            
        Returns:
            List of category names from root to leaf
        """
        try:
            with self.db.cursor() as cur:
                path = []
                current_id = category_id
                
                # Walk up the hierarchy
                while current_id:
                    cur.execute("""
                        SELECT id, name, parent_id
                        FROM clan_categories
                        WHERE id = %s
                    """, (current_id,))
                    
                    row = cur.fetchone()
                    if not row:
                        break
                    
                    # Handle both dict and tuple row formats
                    if isinstance(row, dict):
                        name = row.get('name')
                        parent_id = row.get('parent_id')
                    else:
                        name = row[1] if len(row) > 1 else None
                        parent_id = row[2] if len(row) > 2 else None
                    
                    if name:
                        path.insert(0, name)
                    current_id = parent_id
                
                return path
        except Exception as e:
            logger.error(f"Error getting category path for {category_id}: {e}")
            return []
    
    def aggregate_category_data(self, category_id: int) -> Dict:
        """
        Aggregate product data from category for LLM analysis.
        
        Args:
            category_id: Category ID
            
        Returns:
            Dictionary with aggregated data:
            {
                'product_names': [list],
                'producer_names': [list],
                'descriptions': [list],
                'product_count': int
            }
        """
        try:
            with self.db.cursor() as cur:
                cur.execute("""
                    SELECT name, supplier_name, description
                    FROM clan_products
                    WHERE category_ids @> %s::jsonb
                    LIMIT 20
                """, (f'[{category_id}]',))
                
                products = cur.fetchall()
                
                product_names = []
                producer_names = []
                descriptions = []
                
                for product in products:
                    if isinstance(product, dict):
                        name = product.get('name')
                        supplier = product.get('supplier_name')
                        desc = product.get('description')
                    else:
                        name = product[0] if len(product) > 0 else None
                        supplier = product[1] if len(product) > 1 else None
                        desc = product[2] if len(product) > 2 else None
                    
                    if name:
                        product_names.append(name)
                    if supplier:
                        producer_names.append(supplier)
                    if desc:
                        # Clean HTML from description
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(desc, 'html.parser')
                        clean_desc = soup.get_text()[:500]  # First 500 chars
                        descriptions.append(clean_desc)
                
                return {
                    'product_names': product_names[:10],  # Limit for LLM
                    'producer_names': list(set(producer_names))[:10],
                    'descriptions': descriptions[:5],  # First 5 descriptions
                    'product_count': len(products)
                }
        except Exception as e:
            logger.error(f"Error aggregating category data for {category_id}: {e}")
            return {'product_names': [], 'producer_names': [], 'descriptions': [], 'product_count': 0}
    
    def llm_analyze_category(self, category_name: str, hierarchy_context: str, 
                             product_data: Dict) -> Optional[Dict]:
        """
        Use LLM to analyze category for historical/cultural significance.
        
        Args:
            category_name: Category name
            hierarchy_context: Category hierarchy path (e.g., "Homeware > Plaques")
            product_data: Aggregated product data
            
        Returns:
            Dictionary with LLM analysis or None if LLM unavailable
        """
        if not self.llm_service:
            logger.warning("LLM service not available")
            return None
        
        try:
            prompt = f"""Analyze this product category for historical and cultural significance in Scottish heritage:

Category: {category_name}
Hierarchy: {hierarchy_context}
Products in category: {', '.join(product_data['product_names'][:10])}
Producers: {', '.join(product_data['producer_names'][:5])}
Sample descriptions: {product_data['descriptions'][0] if product_data['descriptions'] else 'N/A'}

Provide a JSON response with:
1. historical_origins: A brief overview of when and how this product category emerged in Scotland
2. cultural_significance: What this category means in Scottish culture and heritage
3. evolution: How the category has evolved over time
4. scottish_heritage_connections: Specific connections to Scottish traditions, clans, or regions

Return only valid JSON, no markdown formatting."""

            messages = [
                {'role': 'system', 'content': 'You are a Scottish heritage and cultural expert. Provide accurate, well-researched information about Scottish products and traditions.'},
                {'role': 'user', 'content': prompt}
            ]
            
            import os
            # Try OpenAI first, fallback to Ollama
            result = self.llm_service.execute_llm_request(
                provider='openai',
                model='gpt-4',
                messages=messages,
                api_key=os.getenv('OPENAI_API_KEY')
            )
            
            if result and 'error' in result:
                # Try Ollama as fallback
                result = self.llm_service.execute_llm_request(
                    provider='ollama',
                    model='llama3.1:70b',
                    messages=messages
                )
            
            if 'error' in result:
                logger.error(f"LLM analysis failed: {result['error']}")
                return None
            
            content = result.get('content', '')
            
            # Try to extract JSON from response
            try:
                # Remove markdown code blocks if present
                content = content.strip()
                if content.startswith('```'):
                    lines = content.split('\n')
                    content = '\n'.join(lines[1:-1])
                
                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                logger.warning("LLM returned non-JSON response, creating structured response")
                # Create structured response from text
                return {
                    'historical_origins': content[:500] if len(content) > 500 else content,
                    'cultural_significance': '',
                    'evolution': '',
                    'scottish_heritage_connections': ''
                }
                
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def web_research_category(self, category_name: str) -> Dict:
        """
        Perform web research on category (placeholder - would use web search API).
        
        Args:
            category_name: Category name
            
        Returns:
            Dictionary with web research results
        """
        # Placeholder implementation
        # In production, this would use a web search API (Google, Bing, etc.)
        # to find relevant articles, Wikipedia entries, etc.
        
        logger.info(f"Web research for category: {category_name}")
        
        # For now, return empty results
        # This would be implemented with actual web search API
        return {
            'sources': [],
            'summary': None
        }
    
    def derive_category_context(self, category_id: int) -> Dict:
        """
        Derive complete category context (LLM + web research + hierarchy).
        
        Args:
            category_id: Category ID
            
        Returns:
            Dictionary with complete heritage data
        """
        try:
            # Get category info
            with self.db.cursor() as cur:
                cur.execute("""
                    SELECT id, name, description, parent_id
                    FROM clan_categories
                    WHERE id = %s
                """, (category_id,))
                row = cur.fetchone()
                
                if not row:
                    logger.error(f"Category {category_id} not found")
                    return {}
                
                # Handle both dict and tuple row formats
                if isinstance(row, dict):
                    category_name = row.get('name')
                    category_desc = row.get('description')
                else:
                    category_name = row[1] if len(row) > 1 else None
                    category_desc = row[2] if len(row) > 2 else None
            
            # Get hierarchy context
            category_path = self.get_category_path(category_id)
            hierarchy_context = ' > '.join(category_path) if category_path else category_name
            
            # Aggregate product data
            product_data = self.aggregate_category_data(category_id)
            
            # LLM analysis
            llm_analysis = self.llm_analyze_category(category_name, hierarchy_context, product_data)
            
            # Web research
            web_research = self.web_research_category(category_name)
            
            # Combine results
            heritage_data = {
                'historical_origins': llm_analysis.get('historical_origins', '') if llm_analysis else '',
                'cultural_significance': llm_analysis.get('cultural_significance', '') if llm_analysis else '',
                'evolution': llm_analysis.get('evolution', '') if llm_analysis else '',
                'scottish_heritage_connections': llm_analysis.get('scottish_heritage_connections', '') if llm_analysis else '',
                'hierarchy_context': hierarchy_context,
                'llm_analysis': llm_analysis or {},
                'web_research': web_research,
                'validated_at': datetime.now().isoformat()
            }
            
            return heritage_data
            
        except Exception as e:
            logger.error(f"Error deriving category context for {category_id}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def save_heritage_data(self, category_id: int, heritage_data: Dict) -> bool:
        """
        Save heritage data to database.
        
        Args:
            category_id: Category ID
            heritage_data: Heritage data dictionary
            
        Returns:
            True if successful
        """
        try:
            import json
            with self.db.cursor() as cur:
                cur.execute("""
                    UPDATE clan_categories
                    SET heritage_data = %s,
                        llm_analyzed_at = NOW(),
                        web_researched_at = NOW()
                    WHERE id = %s
                """, (json.dumps(heritage_data), category_id))
                
                self.db.commit()
            
            logger.info(f"Saved heritage data for category {category_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving heritage data: {e}")
            return False


def derive_category_context(category_id: int, db_connection=None) -> Dict:
    """
    Convenience function to derive category context.
    
    Args:
        category_id: Category ID
        db_connection: Database connection (if None, will create new)
        
    Returns:
        Dictionary with heritage data
    """
    import os
    if db_connection is None:
        from config.database import db_manager
        db_connection = db_manager.get_connection()
    
    researcher = CategoryHeritageResearcher(db_connection)
    return researcher.derive_category_context(category_id)


if __name__ == '__main__':
    import sys
    import os
    from config.database import db_manager
    
    if len(sys.argv) > 1:
        category_id = int(sys.argv[1])
        conn = db_manager.get_connection()
        researcher = CategoryHeritageResearcher(conn)
        
        heritage_data = researcher.derive_category_context(category_id)
        
        print(f"\nHeritage data for category {category_id}:")
        print(json.dumps(heritage_data, indent=2))
        
        # Optionally save
        if len(sys.argv) > 2 and sys.argv[2] == '--save':
            researcher.save_heritage_data(category_id, heritage_data)
            print("\n✓ Heritage data saved to database")
    else:
        print("Usage: python category_heritage_research.py <category_id> [--save]")
        print("Example: python category_heritage_research.py 123 --save")

