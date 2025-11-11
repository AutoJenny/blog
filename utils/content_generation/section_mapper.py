"""
Section Mapper Module

Maps product data to the 7-section structure for generated product posts.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SectionMapper:
    """Maps CLAN product data to the 7-section structure for product articles."""
    
    # Define the 7 sections for generated product posts
    SECTIONS = [
        {
            'id': 'section_1',
            'name': 'Introduction & Historical Context',
            'type': 'introduction_historical_context'
        },
        {
            'id': 'section_2',
            'name': 'Craftsmanship & Materials',
            'type': 'craftsmanship_materials'
        },
        {
            'id': 'section_3',
            'name': 'Features & Specifications',
            'type': 'features_specifications'
        },
        {
            'id': 'section_4',
            'name': 'How to Use / Practical Guide',
            'type': 'how_to_use'
        },
        {
            'id': 'section_5',
            'name': 'Benefits & Value',
            'type': 'benefits_value'
        },
        {
            'id': 'section_6',
            'name': 'Alternative Products',
            'type': 'alternative_products'
        },
        {
            'id': 'section_7',
            'name': 'Conclusion / Call to Action',
            'type': 'conclusion_cta'
        }
    ]
    
    def map_data_to_sections(self, product_data: Dict) -> Dict:
        """
        Map product data to 7-section structure.
        
        Args:
            product_data: Product data dictionary from ClanDataExtractor
            
        Returns:
            Dictionary mapping section IDs to data sources and metadata
        """
        mapping = {}
        
        # Section 1: Introduction & Historical Context
        mapping['section_1'] = self._map_introduction_historical_context(product_data)
        
        # Section 2: Craftsmanship & Materials
        mapping['section_2'] = self._map_craftsmanship_materials(product_data)
        
        # Section 3: Features & Specifications
        mapping['section_3'] = self._map_features_specifications(product_data)
        
        # Section 4: How to Use / Practical Guide
        mapping['section_4'] = self._map_how_to_use(product_data)
        
        # Section 5: Benefits & Value
        mapping['section_5'] = self._map_benefits_value(product_data)
        
        # Section 6: Alternative Products
        mapping['section_6'] = self._map_alternative_products(product_data)
        
        # Section 7: Conclusion / Call to Action
        mapping['section_7'] = self._map_conclusion_cta(product_data)
        
        return mapping
    
    def _map_introduction_historical_context(self, product_data: Dict) -> Dict:
        """Map data for Introduction & Historical Context section."""
        data_sources = []
        total_words = 0
        
        # Primary: heritage_data.historical_origins.narrative
        heritage_data = product_data.get('heritage_data', {})
        if isinstance(heritage_data, dict):
            historical_origins = heritage_data.get('historical_origins', {})
            if isinstance(historical_origins, dict):
                narrative = historical_origins.get('narrative', '')
                if narrative:
                    word_count = len(narrative.split())
                    total_words += word_count
                    data_sources.append({
                        'field': 'heritage_data.historical_origins.narrative',
                        'available': True,
                        'word_count': word_count,
                        'source': 'clan_categories.heritage_data'
                    })
            
            # Secondary: cultural_significance
            cultural_significance = heritage_data.get('cultural_significance', {})
            if isinstance(cultural_significance, dict):
                narrative = cultural_significance.get('narrative', '')
                if narrative:
                    word_count = len(narrative.split())
                    total_words += word_count
                    data_sources.append({
                        'field': 'heritage_data.cultural_significance.narrative',
                        'available': True,
                        'word_count': word_count,
                        'source': 'clan_categories.heritage_data'
                    })
            
            # Secondary: scottish_heritage_connections
            scottish_heritage = heritage_data.get('scottish_heritage_connections', {})
            if isinstance(scottish_heritage, dict):
                narrative = scottish_heritage.get('narrative', '')
                if narrative:
                    word_count = len(narrative.split())
                    total_words += word_count
                    data_sources.append({
                        'field': 'heritage_data.scottish_heritage_connections.narrative',
                        'available': True,
                        'word_count': word_count,
                        'source': 'clan_categories.heritage_data'
                    })
        
        # Context: category description
        categories = product_data.get('categories', [])
        if categories:
            for cat in categories:
                if isinstance(cat, dict) and cat.get('description'):
                    desc = cat.get('description', '')
                    if desc:
                        word_count = len(desc.split())
                        total_words += word_count
                        data_sources.append({
                            'field': f"category_{cat.get('id')}.description",
                            'available': True,
                            'word_count': word_count,
                            'source': 'clan_categories.description'
                        })
        
        # Product level
        product_level = product_data.get('product_level', 'classic')
        data_sources.append({
            'field': 'product_level',
            'available': True,
            'word_count': 0,
            'source': 'clan_products.product_level',
            'value': product_level
        })
        
        # Calculate completeness (0-1 scale)
        completeness = min(1.0, total_words / 500.0) if total_words > 0 else 0.0
        
        return {
            'section_name': 'Introduction & Historical Context',
            'section_type': 'introduction_historical_context',
            'data_sources': data_sources,
            'completeness': round(completeness, 2),
            'llm_role': 'synthesize',
            'llm_needed': True,
            'product_level': product_level
        }
    
    def _map_craftsmanship_materials(self, product_data: Dict) -> Dict:
        """Map data for Craftsmanship & Materials section."""
        data_sources = []
        total_words = 0
        
        # Primary: supplier_description
        supplier_desc = product_data.get('supplier_description', '')
        if supplier_desc:
            # Remove HTML tags for word count
            import re
            text_only = re.sub(r'<[^>]+>', '', supplier_desc)
            word_count = len(text_only.split())
            total_words += word_count
            data_sources.append({
                'field': 'supplier_description',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.supplier_description'
            })
        
        # Secondary: specifications
        specifications = product_data.get('specifications', '')
        if specifications:
            if isinstance(specifications, dict):
                spec_text = str(specifications)
            else:
                spec_text = specifications
            word_count = len(spec_text.split())
            total_words += word_count
            data_sources.append({
                'field': 'specifications',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.specifications'
            })
        
        # Secondary: additional_data (materials)
        additional_data = product_data.get('additional_data', {})
        if isinstance(additional_data, dict):
            # Check for material field
            material = additional_data.get('material', {})
            if isinstance(material, dict) and material.get('value'):
                word_count = len(str(material.get('value', '')).split())
                total_words += word_count
                data_sources.append({
                    'field': 'additional_data.material',
                    'available': True,
                    'word_count': word_count,
                    'source': 'clan_products.additional_data'
                })
        
        # Secondary: supplier_name
        supplier_name = product_data.get('supplier_name', '')
        if supplier_name:
            data_sources.append({
                'field': 'supplier_name',
                'available': True,
                'word_count': 1,  # Just the name
                'source': 'clan_products.supplier_name'
            })
        
        completeness = min(1.0, total_words / 300.0) if total_words > 0 else 0.0
        
        return {
            'section_name': 'Craftsmanship & Materials',
            'section_type': 'craftsmanship_materials',
            'data_sources': data_sources,
            'completeness': round(completeness, 2),
            'llm_role': 'clean_html_format',
            'llm_needed': True
        }
    
    def _map_features_specifications(self, product_data: Dict) -> Dict:
        """Map data for Features & Specifications section."""
        data_sources = []
        total_words = 0
        
        # Primary: description (full HTML)
        description = product_data.get('description', '')
        if description:
            import re
            text_only = re.sub(r'<[^>]+>', '', description)
            word_count = len(text_only.split())
            total_words += word_count
            data_sources.append({
                'field': 'description',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.description'
            })
        
        # Primary: configurable_options
        configurable_options = product_data.get('configurable_options', {})
        if isinstance(configurable_options, dict) and configurable_options:
            options_text = str(configurable_options)
            word_count = len(options_text.split())
            total_words += word_count
            data_sources.append({
                'field': 'configurable_options',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.configurable_options'
            })
        
        # Secondary: specifications
        specifications = product_data.get('specifications', '')
        if specifications:
            if isinstance(specifications, dict):
                spec_text = str(specifications)
            else:
                spec_text = specifications
            word_count = len(spec_text.split())
            total_words += word_count
            data_sources.append({
                'field': 'specifications',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.specifications'
            })
        
        # Secondary: additional_data
        additional_data = product_data.get('additional_data', {})
        if isinstance(additional_data, dict) and additional_data:
            data_text = str(additional_data)
            word_count = len(data_text.split())
            total_words += word_count
            data_sources.append({
                'field': 'additional_data',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.additional_data'
            })
        
        # Secondary: dimensions
        dimensions = product_data.get('dimensions', '')
        if dimensions:
            word_count = len(dimensions.split())
            total_words += word_count
            data_sources.append({
                'field': 'dimensions',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.dimensions'
            })
        
        completeness = min(1.0, total_words / 400.0) if total_words > 0 else 0.0
        
        # Product level
        product_level = product_data.get('product_level', 'classic')
        data_sources.append({
            'field': 'product_level',
            'available': True,
            'word_count': 0,
            'source': 'clan_products.product_level',
            'value': product_level
        })
        
        return {
            'section_name': 'Features & Specifications',
            'section_type': 'features_specifications',
            'data_sources': data_sources,
            'completeness': round(completeness, 2),
            'llm_role': 'clean_html_format',
            'llm_needed': True,
            'product_level': product_level
        }
    
    def _map_how_to_use(self, product_data: Dict) -> Dict:
        """Map data for How to Use / Practical Guide section."""
        data_sources = []
        total_words = 0
        
        # Primary: description (if includes usage/styling)
        description = product_data.get('description', '')
        if description:
            # Check if description mentions usage, styling, wear, etc.
            usage_keywords = ['wear', 'style', 'use', 'occasion', 'pair', 'match', 'care']
            import re
            text_lower = re.sub(r'<[^>]+>', '', description).lower()
            if any(keyword in text_lower for keyword in usage_keywords):
                word_count = len(re.sub(r'<[^>]+>', '', description).split())
                total_words += word_count
                data_sources.append({
                    'field': 'description (usage/styling)',
                    'available': True,
                    'word_count': word_count,
                    'source': 'clan_products.description'
                })
        
        # Secondary: heritage_data (cultural use patterns)
        heritage_data = product_data.get('heritage_data', {})
        if isinstance(heritage_data, dict):
            cultural_significance = heritage_data.get('cultural_significance', {})
            if isinstance(cultural_significance, dict):
                narrative = cultural_significance.get('narrative', '')
                if narrative and ('use' in narrative.lower() or 'wear' in narrative.lower()):
                    word_count = len(narrative.split())
                    total_words += word_count
                    data_sources.append({
                        'field': 'heritage_data.cultural_significance (use patterns)',
                        'available': True,
                        'word_count': word_count,
                        'source': 'clan_categories.heritage_data'
                    })
        
        completeness = min(1.0, total_words / 200.0) if total_words > 0 else 0.0
        
        return {
            'section_name': 'How to Use / Practical Guide',
            'section_type': 'how_to_use',
            'data_sources': data_sources,
            'completeness': round(completeness, 2),
            'llm_role': 'generate',
            'llm_needed': True
        }
    
    def _map_benefits_value(self, product_data: Dict) -> Dict:
        """Map data for Benefits & Value section."""
        data_sources = []
        total_words = 0
        
        # Primary: supplier_description (quality, craftsmanship)
        supplier_desc = product_data.get('supplier_description', '')
        if supplier_desc:
            import re
            text_only = re.sub(r'<[^>]+>', '', supplier_desc)
            word_count = len(text_only.split())
            total_words += word_count
            data_sources.append({
                'field': 'supplier_description',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.supplier_description'
            })
        
        # Primary: description (benefits)
        description = product_data.get('description', '')
        if description:
            import re
            text_only = re.sub(r'<[^>]+>', '', description)
            word_count = len(text_only.split())
            total_words += word_count
            data_sources.append({
                'field': 'description',
                'available': True,
                'word_count': word_count,
                'source': 'clan_products.description'
            })
        
        # Secondary: heritage_data (heritage value)
        heritage_data = product_data.get('heritage_data', {})
        if isinstance(heritage_data, dict):
            # Check all heritage dimensions for value-related content
            for key in ['historical_origins', 'cultural_significance', 'scottish_heritage_connections']:
                heritage_dim = heritage_data.get(key, {})
                if isinstance(heritage_dim, dict):
                    narrative = heritage_dim.get('narrative', '')
                    if narrative:
                        word_count = len(narrative.split())
                        total_words += word_count
                        data_sources.append({
                            'field': f'heritage_data.{key}.narrative',
                            'available': True,
                            'word_count': word_count,
                            'source': 'clan_categories.heritage_data'
                        })
        
        # Context: price
        price = product_data.get('price', '')
        if price:
            data_sources.append({
                'field': 'price',
                'available': True,
                'word_count': 1,
                'source': 'clan_products.price'
            })
        
        completeness = min(1.0, total_words / 300.0) if total_words > 0 else 0.0
        
        # Product level
        product_level = product_data.get('product_level', 'classic')
        data_sources.append({
            'field': 'product_level',
            'available': True,
            'word_count': 0,
            'source': 'clan_products.product_level',
            'value': product_level
        })
        
        return {
            'section_name': 'Benefits & Value',
            'section_type': 'benefits_value',
            'data_sources': data_sources,
            'completeness': round(completeness, 2),
            'llm_role': 'extract_synthesize',
            'llm_needed': True,
            'product_level': product_level
        }
    
    def _map_alternative_products(self, product_data: Dict) -> Dict:
        """Map data for Alternative Products section."""
        data_sources = []
        
        # Note: Alternative products are found via find_alternative_products() method
        # This is called separately, not stored in product_data
        # We mark it as available if product has category_ids
        category_ids = product_data.get('category_ids', [])
        if category_ids:
            data_sources.append({
                'field': 'find_alternative_products()',
                'available': True,
                'word_count': 0,  # Method call, not text
                'source': 'ClanDataExtractor.find_alternative_products()'
            })
        
        return {
            'section_name': 'Alternative Products',
            'section_type': 'alternative_products',
            'data_sources': data_sources,
            'completeness': 1.0 if category_ids else 0.0,
            'llm_role': 'generate_comparison',
            'llm_needed': True
        }
    
    def _map_conclusion_cta(self, product_data: Dict) -> Dict:
        """Map data for Conclusion / Call to Action section."""
        data_sources = []
        
        # Primary: product name
        name = product_data.get('name', '')
        if name:
            data_sources.append({
                'field': 'name',
                'available': True,
                'word_count': len(name.split()),
                'source': 'clan_products.name'
            })
        
        # Primary: url (product page link)
        url = product_data.get('url', '')
        if url:
            data_sources.append({
                'field': 'url',
                'available': True,
                'word_count': 0,
                'source': 'clan_products.url'
            })
        
        # Secondary: category links (from categories)
        categories = product_data.get('categories', [])
        if categories:
            data_sources.append({
                'field': 'categories',
                'available': True,
                'word_count': len(categories),
                'source': 'clan_categories'
            })
        
        completeness = 1.0 if (name and url) else 0.5 if name else 0.0
        
        # Product level
        product_level = product_data.get('product_level', 'classic')
        data_sources.append({
            'field': 'product_level',
            'available': True,
            'word_count': 0,
            'source': 'clan_products.product_level',
            'value': product_level
        })
        
        return {
            'section_name': 'Conclusion / Call to Action',
            'section_type': 'conclusion_cta',
            'data_sources': data_sources,
            'completeness': round(completeness, 2),
            'llm_role': 'generate_summary_cta',
            'llm_needed': True,
            'product_level': product_level
        }

