"""
Rota Generator Module

Generates diverse weekly rota ensuring non-repetition and variety.
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Optional
from config.database import db_manager
from .diversity import DiversityManager

logger = logging.getLogger(__name__)


class RotaGenerator:
    """
    Generates diverse weekly rota ensuring non-repetition and variety.
    """
    
    def __init__(self):
        """Initialize rota generator."""
        self.diversity_manager = DiversityManager()
    
    def generate_rota(self,
                     start_date: date,
                     weeks: Optional[int] = None,
                     lookback_weeks: int = 6,
                     min_similarity_gap: float = 0.7,
                     include_all_topics: bool = True) -> List[Dict]:
        """
        Generate weekly rota with diversity constraints.
        
        Args:
            start_date: First Monday of rota
            weeks: Number of weeks to schedule (None = auto-calculate to include all topics)
            lookback_weeks: How many recent weeks to check for diversity
            min_similarity_gap: Minimum similarity threshold to avoid (0.0-1.0)
            include_all_topics: If True and weeks=None, generate rota to include all topics
        
        Returns:
            List of rota entry dictionaries
        """
        # Get active topics first to determine weeks if needed
        topics = self._get_active_topics()
        
        if not topics:
            logger.warning("No active topics found - cannot generate rota")
            return []
        
        # Auto-calculate weeks to include all topics if requested
        if weeks is None and include_all_topics:
            weeks = len(topics)
            logger.info(f"Auto-calculating weeks to include all {len(topics)} topics: {weeks} weeks ({weeks/52:.1f} years)")
        elif weeks is None:
            weeks = 52  # Default to 1 year
        
        logger.info(f"Generating rota for {weeks} weeks starting from {start_date}")
        logger.info(f"Found {len(topics)} active topics")
        
        # Get recent rota history
        recent_topics = self._get_recent_topics(lookback_weeks)
        
        # Track which topics have been used (for ensuring all topics are included)
        used_topic_ids = set()
        unused_topics = topics.copy()
        
        rota = []
        current_date = start_date
        
        # Ensure start_date is a Monday
        if current_date.weekday() != 0:  # 0 = Monday
            days_until_monday = (7 - current_date.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            current_date += timedelta(days=days_until_monday)
            logger.info(f"Adjusted start date to Monday: {current_date}")
        
        for week_num in range(weeks):
            # Calculate diversity scores for all candidates
            candidates = []
            
            # If we want to include all topics, prioritize unused ones
            if include_all_topics and unused_topics:
                # First, try to use topics that haven't been used yet
                for topic in unused_topics:
                    # Skip if topic was used recently
                    if self._was_used_recently(topic['id'], recent_topics, lookback_weeks):
                        continue
                    
                    # Calculate diversity score
                    diversity_score = self.diversity_manager.calculate_diversity(
                        topic,
                        recent_topics,
                        min_similarity_gap
                    )
                    
                    candidates.append({
                        'topic': topic,
                        'diversity_score': diversity_score,
                        'is_unused': True
                    })
            
            # If no unused candidates or we've used all topics, consider all topics
            if not candidates or (include_all_topics and not unused_topics):
                for topic in topics:
                    # Skip if topic was used recently
                    if self._was_used_recently(topic['id'], recent_topics, lookback_weeks):
                        continue
                    
                    # Skip if we already have this in candidates
                    if any(c['topic']['id'] == topic['id'] for c in candidates):
                        continue
                    
                    # Calculate diversity score
                    diversity_score = self.diversity_manager.calculate_diversity(
                        topic,
                        recent_topics,
                        min_similarity_gap
                    )
                    
                    candidates.append({
                        'topic': topic,
                        'diversity_score': diversity_score,
                        'is_unused': False
                    })
            
            if not candidates:
                # Fallback: reset recent topics if no candidates
                logger.warning(f"No candidates for week {week_num + 1}, resetting recent topics")
                recent_topics = []
                candidates = [{'topic': t, 'diversity_score': 1.0, 'is_unused': t['id'] not in used_topic_ids} for t in topics]
            
            # Select topic (weighted random favoring diversity and unused topics)
            selected = self._select_topic(candidates, prefer_unused=include_all_topics)
            
            # Track usage
            used_topic_ids.add(selected['topic']['id'])
            if include_all_topics:
                unused_topics = [t for t in unused_topics if t['id'] != selected['topic']['id']]
            
            # Get ISO week info
            iso_year, iso_week, _ = current_date.isocalendar()
            
            # Create rota entry
            rota_entry = {
                'topic_id': selected['topic']['id'],
                'scheduled_year': iso_year,
                'scheduled_week': iso_week,
                'scheduled_date': current_date,
                'diversity_score': selected['diversity_score'],
                'status': 'scheduled'
            }
            
            rota.append(rota_entry)
            
            # Update recent topics
            recent_topics.append(selected['topic'])
            if len(recent_topics) > lookback_weeks:
                recent_topics.pop(0)
            
            # Move to next week (Monday)
            current_date += timedelta(days=7)
        
        logger.info(f"Generated {len(rota)} rota entries")
        if include_all_topics:
            logger.info(f"Used {len(used_topic_ids)} unique topics out of {len(topics)} available")
            if len(used_topic_ids) < len(topics):
                logger.warning(f"Not all topics were used ({len(topics) - len(used_topic_ids)} unused)")
        
        return rota
    
    def _get_active_topics(self) -> List[Dict]:
        """
        Get all active topics from database.
        
        Returns:
            List of topic dictionaries
        """
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, topic_name, topic_description, topic_keywords,
                        embedding_vector, article_ids, category_ids,
                        topic_type, priority, is_active
                    FROM kb_topics
                    WHERE is_active = TRUE
                    ORDER BY priority DESC, id
                """)
                
                topics = cursor.fetchall()
                
                # Convert to list of dicts and parse arrays
                result = []
                for topic in topics:
                    topic_dict = dict(topic)
                    # Convert numpy arrays if needed
                    if isinstance(topic_dict.get('embedding_vector'), list):
                        topic_dict['centroid_embedding'] = topic_dict['embedding_vector']
                    elif topic_dict.get('embedding_vector') is not None:
                        import numpy as np
                        topic_dict['centroid_embedding'] = np.array(topic_dict['embedding_vector']).tolist()
                    else:
                        topic_dict['centroid_embedding'] = None
                    
                    result.append(topic_dict)
                
                return result
        except Exception as e:
            logger.error(f"Error getting active topics: {e}")
            return []
    
    def _get_recent_topics(self, lookback_weeks: int) -> List[Dict]:
        """
        Get topics from recent rota history.
        
        Args:
            lookback_weeks: Number of weeks to look back
        
        Returns:
            List of recent topic dictionaries
        """
        try:
            cutoff_date = date.today() - timedelta(weeks=lookback_weeks)
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT t.id, t.topic_name, t.topic_type,
                           t.embedding_vector, t.category_ids, r.scheduled_date
                    FROM kb_topic_rota r
                    JOIN kb_topics t ON r.topic_id = t.id
                    WHERE r.scheduled_date >= %s
                    ORDER BY r.scheduled_date DESC
                """, (cutoff_date,))
                
                recent = cursor.fetchall()
                
                # Convert to list of dicts
                result = []
                for topic in recent:
                    topic_dict = dict(topic)
                    # Parse embedding vector
                    if isinstance(topic_dict.get('embedding_vector'), list):
                        topic_dict['centroid_embedding'] = topic_dict['embedding_vector']
                    elif topic_dict.get('embedding_vector') is not None:
                        import numpy as np
                        topic_dict['centroid_embedding'] = np.array(topic_dict['embedding_vector']).tolist()
                    
                    result.append(topic_dict)
                
                return result
        except Exception as e:
            logger.warning(f"Error getting recent topics: {e}")
            return []
    
    def _was_used_recently(self, topic_id: int, recent_topics: List[Dict],
                          lookback_weeks: int) -> bool:
        """
        Check if topic was used recently.
        
        Args:
            topic_id: Topic ID to check
            recent_topics: List of recent topics
            lookback_weeks: Number of weeks to check
        
        Returns:
            True if topic was used recently
        """
        return any(t.get('id') == topic_id for t in recent_topics)
    
    def _select_topic(self, candidates: List[Dict], prefer_unused: bool = False) -> Dict:
        """
        Select topic from candidates using weighted random (favoring diversity and unused topics).
        
        Args:
            candidates: List of candidate dicts with 'topic', 'diversity_score', and optionally 'is_unused'
            prefer_unused: If True, give higher weight to unused topics
        
        Returns:
            Selected candidate dictionary
        """
        if not candidates:
            raise ValueError("No candidates provided")
        
        # Weight by diversity score (higher = more likely)
        import random
        
        # Normalize diversity scores to probabilities
        scores = [c['diversity_score'] for c in candidates]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All same score, normalize to 1.0
            normalized = [1.0] * len(scores)
        else:
            # Normalize to [0, 1] range
            normalized = [(s - min_score) / (max_score - min_score) for s in scores]
        
        # Square to favor higher scores more
        weights = [s ** 2 for s in normalized]
        
        # Boost weight for unused topics if requested
        if prefer_unused:
            for i, candidate in enumerate(candidates):
                if candidate.get('is_unused', False):
                    weights[i] *= 2.0  # Double the weight for unused topics
        
        # Weighted random selection
        selected = random.choices(candidates, weights=weights, k=1)[0]
        
        return selected
    
    def save_rota(self, rota: List[Dict]) -> bool:
        """
        Save rota entries to database.
        
        Args:
            rota: List of rota entry dictionaries
        
        Returns:
            True if successful
        """
        try:
            with db_manager.get_cursor() as cursor:
                for entry in rota:
                    cursor.execute("""
                        INSERT INTO kb_topic_rota 
                            (topic_id, scheduled_week, scheduled_year, scheduled_date,
                             diversity_score, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (scheduled_year, scheduled_week)
                        DO UPDATE SET
                            topic_id = EXCLUDED.topic_id,
                            scheduled_date = EXCLUDED.scheduled_date,
                            diversity_score = EXCLUDED.diversity_score,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        entry['topic_id'],
                        entry['scheduled_week'],
                        entry['scheduled_year'],
                        entry['scheduled_date'],
                        entry['diversity_score'],
                        entry['status']
                    ))
            
            logger.info(f"Saved {len(rota)} rota entries to database")
            return True
        except Exception as e:
            logger.error(f"Error saving rota: {e}")
            return False
