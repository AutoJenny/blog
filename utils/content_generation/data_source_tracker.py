"""
Data Source Tracker

Tracks which data sources (CLAN vs LLM) were used for each section of generated content.
"""

import logging
import json
from typing import Dict, List, Optional
from config.database import db_manager

logger = logging.getLogger(__name__)


class DataSourceTracker:
    """Tracks data sources used in generated content."""
    
    def __init__(self):
        self.llm_threshold = 50  # Configurable threshold for LLM supplementation
    
    def create_tracking_structure(self, post_id: int, product_id: int, 
                                 validation_report: Dict) -> Dict:
        """
        Create initial tracking structure for a post.
        
        Args:
            post_id: Post ID
            product_id: Product ID
            validation_report: Validation report from ClanDataExtractor
            
        Returns:
            Tracking structure dictionary
        """
        return {
            'post_id': post_id,
            'product_id': product_id,
            'data_completeness': {
                'core_completeness': validation_report.get('core_completeness', 0.0),
                'optional_completeness': validation_report.get('optional_completeness', 0.0),
                'has_minimum_requirements': validation_report.get('has_minimum_requirements', False)
            },
            'sections': {},
            'llm_supplementation': validation_report.get('needs_llm_supplement', {}),
            'validation_timestamp': None
        }
    
    def track_section_data_source(self, post_id: int, section_id: int, 
                                 section_number: int, section_name: str,
                                 clan_data_sources: List[str],
                                 llm_supplemented: bool = False) -> None:
        """
        Track data sources for a specific section.
        
        Args:
            post_id: Post ID
            section_id: Section ID
            section_number: Section number (1-7)
            section_name: Section name
            clan_data_sources: List of CLAN data sources used (e.g., ['product.description', 'heritage_data.historical_origins'])
            llm_supplemented: Whether LLM supplementation was used
        """
        try:
            # Get existing tracking data
            tracking_data = self.get_tracking_data(post_id)
            
            # Update section tracking
            tracking_data['sections'][str(section_id)] = {
                'section_number': section_number,
                'section_name': section_name,
                'clan_data_sources': clan_data_sources,
                'llm_supplemented': llm_supplemented,
                'data_source_ratio': self._calculate_data_source_ratio(clan_data_sources, llm_supplemented)
            }
            
            # Save to database
            self.save_tracking_data(post_id, tracking_data)
            
        except Exception as e:
            logger.error(f"Error tracking section data source for section {section_id}: {e}")
    
    def _calculate_data_source_ratio(self, clan_sources: List[str], 
                                    llm_supplemented: bool) -> Dict:
        """
        Calculate the ratio of CLAN vs LLM data sources.
        
        Args:
            clan_sources: List of CLAN data sources
            llm_supplemented: Whether LLM was used
            
        Returns:
            Dictionary with ratio information
        """
        clan_count = len(clan_sources)
        llm_count = 1 if llm_supplemented else 0
        total = clan_count + llm_count
        
        if total == 0:
            return {
                'clan_percentage': 0.0,
                'llm_percentage': 0.0,
                'primary_source': 'unknown'
            }
        
        clan_pct = (clan_count / total) * 100
        llm_pct = (llm_count / total) * 100
        
        return {
            'clan_percentage': clan_pct,
            'llm_percentage': llm_pct,
            'primary_source': 'clan' if clan_pct > llm_pct else 'llm',
            'clan_sources_count': clan_count,
            'llm_sources_count': llm_count
        }
    
    def get_tracking_data(self, post_id: int) -> Dict:
        """
        Get tracking data for a post.
        
        Args:
            post_id: Post ID
            
        Returns:
            Tracking data dictionary
        """
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT meta_info FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                if result and result.get('meta_info'):
                    meta_info = result['meta_info']
                    if isinstance(meta_info, str):
                        meta_info = json.loads(meta_info)
                    
                    # Check if tracking data exists
                    if isinstance(meta_info, dict) and 'data_source_tracking' in meta_info:
                        return meta_info['data_source_tracking']
                
                # Return empty structure if not found
                return {
                    'post_id': post_id,
                    'product_id': None,
                    'data_completeness': {},
                    'sections': {},
                    'llm_supplementation': {}
                }
        except Exception as e:
            logger.error(f"Error getting tracking data for post {post_id}: {e}")
            return {
                'post_id': post_id,
                'product_id': None,
                'data_completeness': {},
                'sections': {},
                'llm_supplementation': {}
            }
    
    def save_tracking_data(self, post_id: int, tracking_data: Dict) -> None:
        """
        Save tracking data to post_development.meta_info.
        
        Args:
            post_id: Post ID
            tracking_data: Tracking data dictionary
        """
        try:
            with db_manager.get_cursor() as cursor:
                # Get existing meta_info
                cursor.execute("""
                    SELECT meta_info FROM post_development
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cursor.fetchone()
                if result:
                    meta_info = result.get('meta_info') or {}
                    if isinstance(meta_info, str):
                        meta_info = json.loads(meta_info) if meta_info else {}
                    elif meta_info is None:
                        meta_info = {}
                else:
                    meta_info = {}
                
                # Update with tracking data
                meta_info['data_source_tracking'] = tracking_data
                
                # Save back to database
                cursor.execute("""
                    UPDATE post_development
                    SET meta_info = %s::jsonb, updated_at = CURRENT_TIMESTAMP
                    WHERE post_id = %s
                """, (json.dumps(meta_info), post_id))
                
                logger.debug(f"Saved tracking data for post {post_id}")
        except Exception as e:
            logger.error(f"Error saving tracking data for post {post_id}: {e}")
    
    def validate_pre_generation(self, product_data: Dict, validation_report: Dict) -> Dict:
        """
        Validate product data before generation (pre-generation checks).
        
        Args:
            product_data: Product data from ClanDataExtractor
            validation_report: Validation report from ClanDataExtractor
            
        Returns:
            Validation result dictionary
        """
        has_minimum = validation_report.get('has_minimum_requirements', False)
        missing_fields = validation_report.get('missing_fields', [])
        core_completeness = validation_report.get('core_completeness', 0.0)
        
        validation_result = {
            'valid': has_minimum,
            'missing_fields': missing_fields,
            'core_completeness': core_completeness,
            'warnings': [],
            'can_proceed': has_minimum
        }
        
        if not has_minimum:
            validation_result['warnings'].append(
                f"Missing required fields: {', '.join(missing_fields)}. "
                "Generation may produce incomplete content."
            )
        
        if core_completeness < 1.0:
            validation_result['warnings'].append(
                f"Core data completeness is {core_completeness * 100:.1f}%. "
                "Some sections may require LLM supplementation."
            )
        
        return validation_result
    
    def validate_post_generation(self, post_id: int) -> Dict:
        """
        Validate generated content after generation (post-generation checks).
        
        Args:
            post_id: Post ID
            
        Returns:
            Validation result dictionary
        """
        try:
            tracking_data = self.get_tracking_data(post_id)
            
            if not tracking_data.get('sections'):
                return {
                    'valid': False,
                    'error': 'No tracking data found for sections',
                    'clan_usage_score': 0.0,
                    'llm_supplementation_count': 0,
                    'warnings': []
                }
            
            sections = tracking_data.get('sections', {})
            total_sections = len(sections)
            llm_supplemented_count = sum(
                1 for s in sections.values() if s.get('llm_supplemented', False)
            )
            
            # Calculate CLAN usage score
            clan_scores = []
            for section_data in sections.values():
                ratio = section_data.get('data_source_ratio', {})
                clan_pct = ratio.get('clan_percentage', 0.0)
                clan_scores.append(clan_pct)
            
            avg_clan_usage = sum(clan_scores) / len(clan_scores) if clan_scores else 0.0
            
            warnings = []
            if avg_clan_usage < 50.0:
                warnings.append(
                    f"Low CLAN data usage ({avg_clan_usage:.1f}%). "
                    "Content may rely heavily on LLM supplementation."
                )
            
            if llm_supplemented_count > total_sections * 0.5:
                warnings.append(
                    f"{llm_supplemented_count} of {total_sections} sections used LLM supplementation. "
                    "Consider reviewing for accuracy."
                )
            
            return {
                'valid': True,
                'clan_usage_score': avg_clan_usage,
                'llm_supplementation_count': llm_supplemented_count,
                'total_sections': total_sections,
                'warnings': warnings,
                'sections_summary': {
                    str(sid): {
                        'section_name': s.get('section_name'),
                        'clan_sources': s.get('clan_data_sources', []),
                        'llm_supplemented': s.get('llm_supplemented', False),
                        'clan_percentage': s.get('data_source_ratio', {}).get('clan_percentage', 0.0)
                    }
                    for sid, s in sections.items()
                }
            }
        except Exception as e:
            logger.error(f"Error validating post-generation for post {post_id}: {e}")
            return {
                'valid': False,
                'error': str(e),
                'clan_usage_score': 0.0,
                'llm_supplementation_count': 0,
                'warnings': []
            }
    
    def get_data_source_summary(self, post_id: int) -> Dict:
        """
        Get a summary of data sources used across all sections.
        
        Args:
            post_id: Post ID
            
        Returns:
            Summary dictionary
        """
        tracking_data = self.get_tracking_data(post_id)
        validation_result = self.validate_post_generation(post_id)
        
        return {
            'post_id': post_id,
            'product_id': tracking_data.get('product_id'),
            'data_completeness': tracking_data.get('data_completeness', {}),
            'overall_clan_usage': validation_result.get('clan_usage_score', 0.0),
            'llm_supplementation_count': validation_result.get('llm_supplementation_count', 0),
            'total_sections': validation_result.get('total_sections', 0),
            'warnings': validation_result.get('warnings', []),
            'sections': validation_result.get('sections_summary', {})
        }

