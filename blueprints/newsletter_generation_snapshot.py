"""Newsletter Generation Snapshot Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_generation_snapshot', __name__)


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-news', methods=['GET'])
def generate_news_component(issue_id: int, block_id: int):
    """Generate news component for snapshot block - returns top news items with summaries."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.services.suggestion_service import generate_suggestions
        from newsletter.db.queries_sources import get_cached_items
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Get used news item IDs from previous newsletters (exclude current issue)
        used_item_ids = set()
        try:
            from config.database import db_manager
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all snapshot blocks from other issues that have news_items
                    cur.execute("""
                        SELECT nb.payload_json
                        FROM newsletter_block nb
                        JOIN newsletter_issue ni ON nb.issue_id = ni.id
                        WHERE nb.type = 'snapshot'
                        AND nb.issue_id != %s
                        AND nb.payload_json IS NOT NULL
                        AND nb.payload_json != '{}'::jsonb
                        AND nb.payload_json ? 'news_items'
                    """, (issue_id,))
                    blocks = cur.fetchall()
                    for block_row in blocks:
                        payload = dict(block_row)['payload_json']
                        news_items_list = payload.get('news_items', [])
                        for item in news_items_list:
                            if isinstance(item, dict) and item.get('id'):
                                used_item_ids.add(item['id'])
        except Exception as e:
            logger.warning(f"Error getting used news items: {e}")
        
        # Get top news items (category='news')
        news_items = get_cached_items(category='news', days_back=14, limit=50)  # Get more to filter out used ones
        
        if not news_items:
            return jsonify({
                'success': False,
                'error': 'No news items available',
                'items': []
            })
        
        # Filter out items already used in previous newsletters
        if used_item_ids:
            news_items = [item for item in news_items if item.get('id') not in used_item_ids]
            logger.info(f"Filtered out {len(used_item_ids)} used news items, {len(news_items)} remaining")
        
        if not news_items:
            return jsonify({
                'success': False,
                'error': 'No new news items available (all have been used in previous newsletters)',
                'items': []
            })
        
        # Score and sort by combined_score
        from newsletter.services.scoring import score_items
        from datetime import datetime
        scored = score_items(news_items, reference_date=datetime.now())
        scored.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Take top 5 items
        top_news = scored[:5]
        
        # Format items with summaries
        formatted_items = []
        for item in top_news:
            # Convert datetime to ISO string if present
            published_at = item.get('published_at')
            if published_at and hasattr(published_at, 'isoformat'):
                published_at = published_at.isoformat()
            elif published_at:
                published_at = str(published_at)
            
            formatted_items.append({
                'id': item.get('id'),
                'title': item.get('title', ''),
                'source_name': item.get('source_name', ''),
                'url': item.get('url', ''),
                'summary': item.get('raw_data', {}).get('description', '')[:200] if item.get('raw_data', {}).get('description') else '',
                'published_at': published_at,
                'combined_score': float(item.get('combined_score', 0))
            })
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        payload['news_items'] = formatted_items
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'items': formatted_items
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating news component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-snapshot-events', methods=['GET'])
def generate_snapshot_events_component(issue_id: int, block_id: int):
    """Generate events component for snapshot block - returns top event items with summaries."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from newsletter.db.queries_sources import get_cached_items
        from newsletter.services.scoring import score_items
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Get used event item IDs from previous newsletters (exclude current issue)
        used_item_ids = set()
        try:
            from config.database import db_manager
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all snapshot blocks from other issues that have events_items
                    cur.execute("""
                        SELECT nb.payload_json
                        FROM newsletter_block nb
                        JOIN newsletter_issue ni ON nb.issue_id = ni.id
                        WHERE nb.type = 'snapshot'
                        AND nb.issue_id != %s
                        AND nb.payload_json IS NOT NULL
                        AND nb.payload_json != '{}'::jsonb
                        AND nb.payload_json ? 'events_items'
                    """, (issue_id,))
                    blocks = cur.fetchall()
                    for block_row in blocks:
                        payload = dict(block_row)['payload_json']
                        events_items_list = payload.get('events_items', [])
                        for item in events_items_list:
                            if isinstance(item, dict) and item.get('id'):
                                used_item_ids.add(item['id'])
        except Exception as e:
            logger.warning(f"Error getting used event items: {e}")
        
        # Get top event items (category='event')
        event_items = get_cached_items(category='event', days_back=14, limit=50)  # Get more to filter out used ones
        
        if not event_items:
            return jsonify({
                'success': False,
                'error': 'No event items available',
                'items': []
            })
        
        # Filter out items already used in previous newsletters
        if used_item_ids:
            event_items = [item for item in event_items if item.get('id') not in used_item_ids]
            logger.info(f"Filtered out {len(used_item_ids)} used event items, {len(event_items)} remaining")
        
        if not event_items:
            return jsonify({
                'success': False,
                'error': 'No new event items available (all have been used in previous newsletters)',
                'items': []
            })
        
        # Score and sort by combined_score
        scored = score_items(event_items, reference_date=datetime.now())
        scored.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Take top 5 items
        top_events = scored[:5]
        
        # Format items with summaries
        formatted_items = []
        for item in top_events:
            # Convert datetime to ISO string if present
            event_date = item.get('event_date')
            if event_date and hasattr(event_date, 'isoformat'):
                event_date = event_date.isoformat()
            elif event_date:
                event_date = str(event_date)
            
            formatted_items.append({
                'id': item.get('id'),
                'title': item.get('title', ''),
                'source_name': item.get('source_name', ''),
                'url': item.get('url', ''),
                'location': item.get('location', ''),
                'event_date': event_date,
                'summary': item.get('raw_data', {}).get('description', '')[:200] if item.get('raw_data', {}).get('description') else '',
                'combined_score': float(item.get('combined_score', 0))
            })
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        payload['events_items'] = formatted_items
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'items': formatted_items
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating events component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/compile-snapshot', methods=['POST'])
def compile_snapshot(issue_id: int, block_id: int):
    """Compile news and events into two chatty paragraphs with embedded links using LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from blueprints.header.llm_service import LLMService
        from datetime import datetime
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        payload = block.get('payload_json', {}) or {}
        news_items = payload.get('news_items', [])
        events_items = payload.get('events_items', [])
        round_scotland_items = payload.get('round_scotland_items', [])
        
        if not news_items and not events_items and not round_scotland_items:
            return jsonify({
                'success': False,
                'error': 'No items available. Please generate news, events, and/or Round Scotland components first.',
                'result': None
            })
        
        # Use LLM to generate two chatty paragraphs
        llm_service = LLMService()
        
        # Build context for LLM
        news_context = []
        for item in news_items[:10]:  # Limit to top 10 for context
            news_context.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'source': item.get('source_name', ''),
                'summary': item.get('summary', '')
            })
        
        events_context = []
        for item in events_items[:10]:  # Limit to top 10 for context
            events_context.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'source': item.get('source_name', ''),
                'location': item.get('location', ''),
                'summary': item.get('summary', '')
            })
        
        # Build system prompt based on available components
        has_round_scotland = len(round_scotland_items) > 0
        
        if has_round_scotland:
            system_prompt = """You are a newsletter writer creating a chatty "In the News" section for a Scottish heritage newsletter.

Your task is to write THREE separate paragraphs:
1. NEWS PARAGRAPH: A chatty overview of the news stories, mentioning story titles with embedded markdown links [title](url)
2. EVENTS PARAGRAPH: A chatty overview of the events, mentioning event titles with embedded markdown links [title](url)
3. ROUND SCOTLAND PARAGRAPH: A light-hearted, playful overview of quirky local news stories from around Scotland

IMPORTANT FORMATTING REQUIREMENTS:
- Start your response with exactly "NEWS:" on its own line
- Then write the news paragraph (3-5 sentences, conversational tone)
- Then write exactly "EVENTS:" on its own line  
- Then write the events paragraph (3-5 sentences, conversational tone)
- Then write exactly "ROUND SCOTLAND:" on its own line
- Then write the Round Scotland paragraph (3-5 sentences, playful and light-hearted tone)

Where stories overlap or discuss the same topic, mention them together naturally.
Write in a warm, conversational, engaging tone - like a friend sharing interesting news.
The Round Scotland section should be more playful and charming - think "And finally..." news.
Each paragraph should be 3-5 sentences and flow naturally. Use markdown links: [Story Title](url)"""
        else:
            system_prompt = """You are a newsletter writer creating a chatty "In the News" section for a Scottish heritage newsletter.

Your task is to write TWO separate paragraphs:
1. NEWS PARAGRAPH: A chatty overview of the news stories, mentioning story titles with embedded markdown links [title](url)
2. EVENTS PARAGRAPH: A chatty overview of the events, mentioning event titles with embedded markdown links [title](url)

IMPORTANT FORMATTING REQUIREMENTS:
- Start your response with exactly "NEWS:" on its own line
- Then write the news paragraph (3-5 sentences, conversational tone)
- Then write exactly "EVENTS:" on its own line  
- Then write the events paragraph (3-5 sentences, conversational tone)

Where stories overlap or discuss the same topic, mention them together naturally.
Write in a warm, conversational, engaging tone - like a friend sharing interesting news.
Each paragraph should be 3-5 sentences and flow naturally. Use markdown links: [Story Title](url)"""
        
        # Build user prompt with available components
        prompt_parts = []
        
        if news_context:
            prompt_parts.append("NEWS STORIES TO COVER:")
            prompt_parts.append(chr(10).join([f"- {item['title']} ({item['source']}): {item['url']}" + (f" - {item['summary'][:100]}" if item.get('summary') else "") for item in news_context]))
        
        if events_context:
            prompt_parts.append("\nEVENTS TO COVER:")
            prompt_parts.append(chr(10).join([f"- {item['title']} ({item['source']})" + (f" in {item['location']}" if item.get('location') else "") + f": {item['url']}" + (f" - {item['summary'][:100]}" if item.get('summary') else "") for item in events_context]))
        
        if round_scotland_items:
            prompt_parts.append("\nROUND SCOTLAND STORIES TO COVER:")
            round_scotland_context = []
            for item in round_scotland_items[:10]:
                round_scotland_context.append({
                    'title': item.get('title_internal') or item.get('title', ''),
                    'url': item.get('url', ''),
                    'source': item.get('source_label', ''),
                    'location': item.get('location', ''),
                    'summary': item.get('summary_newsletter', '')
                })
            prompt_parts.append(chr(10).join([f"- {item['title']} ({item['source']})" + (f" in {item['location']}" if item.get('location') else "") + f": {item['url']}" + (f" - {item['summary'][:100]}" if item.get('summary') else "") for item in round_scotland_context]))
        
        if has_round_scotland:
            user_prompt = f"""Create three chatty paragraphs for "In the News" section.

{chr(10).join(prompt_parts)}

REQUIRED OUTPUT FORMAT (follow exactly):
NEWS:
[Write a chatty 3-5 sentence paragraph about the news stories. Mention story titles with markdown links like [Story Title](url). Write conversationally, like sharing interesting news with a friend. If stories are related, mention them together.]

EVENTS:
[Write a chatty 3-5 sentence paragraph about the events. Mention event titles with markdown links like [Event Title](url). Write conversationally about what's happening. If events are related, mention them together.]

ROUND SCOTLAND:
[Write a playful, light-hearted 3-5 sentence paragraph about the quirky local stories. This should be charming and amusing - think "And finally..." news. Mention story titles with markdown links like [Story Title](url). Make it fun and engaging.]

Remember: Start with "NEWS:" on its own line, then the paragraph, then "EVENTS:" on its own line, then the events paragraph, then "ROUND SCOTLAND:" on its own line, then the Round Scotland paragraph."""
        else:
            user_prompt = f"""Create two chatty paragraphs for "In the News" section.

{chr(10).join(prompt_parts)}

REQUIRED OUTPUT FORMAT (follow exactly):
NEWS:
[Write a chatty 3-5 sentence paragraph about the news stories. Mention story titles with markdown links like [Story Title](url). Write conversationally, like sharing interesting news with a friend. If stories are related, mention them together.]

EVENTS:
[Write a chatty 3-5 sentence paragraph about the events. Mention event titles with markdown links like [Event Title](url). Write conversationally about what's happening. If events are related, mention them together.]

Remember: Start with "NEWS:" on its own line, then the paragraph, then "EVENTS:" on its own line, then the events paragraph."""
        
        try:
            logger.info(f"Calling LLM to generate snapshot paragraphs for {len(news_context)} news items and {len(events_context)} events")
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error generating snapshot paragraphs: {result['error']}")
                return jsonify({
                    'success': False,
                    'error': f'LLM generation failed: {result["error"]}. Please try again.',
                    'result': None
                }), 500
            
            response = result.get('content', '').strip()
            logger.info(f"LLM response received: {response[:200] if response else 'None'}...")
            
            # Parse the response to extract paragraphs
            news_paragraph = ""
            events_paragraph = ""
            round_scotland_paragraph = ""
            
            if response:
                response_text = response.strip()
                logger.info(f"Processing LLM response (length: {len(response_text)})")
                
                # Try to split by markers (case insensitive)
                response_upper = response_text.upper()
                has_round_scotland_marker = "ROUND SCOTLAND:" in response_upper or "ROUNDSCOTLAND:" in response_upper
                
                if has_round_scotland_marker and "NEWS:" in response_upper and "EVENTS:" in response_upper:
                    # Three paragraphs: NEWS, EVENTS, ROUND SCOTLAND
                    news_idx = response_text.upper().find("NEWS:")
                    events_idx = response_text.upper().find("EVENTS:")
                    round_scotland_idx = response_text.upper().find("ROUND SCOTLAND:")
                    if round_scotland_idx == -1:
                        round_scotland_idx = response_text.upper().find("ROUNDSCOTLAND:")
                    
                    if news_idx < events_idx < round_scotland_idx:
                        news_paragraph = response_text[news_idx + 5:events_idx].strip()
                        events_paragraph = response_text[events_idx + 7:round_scotland_idx].strip()
                        round_scotland_paragraph = response_text[round_scotland_idx + len("ROUND SCOTLAND:"):].strip()
                        logger.info("Parsed using NEWS:/EVENTS:/ROUND SCOTLAND: markers")
                elif "NEWS:" in response_upper and "EVENTS:" in response_upper:
                    # Two paragraphs: NEWS, EVENTS
                    news_idx = response_text.upper().find("NEWS:")
                    events_idx = response_text.upper().find("EVENTS:")
                    
                    if news_idx < events_idx:
                        news_paragraph = response_text[news_idx + 5:events_idx].strip()
                        events_paragraph = response_text[events_idx + 7:].strip()
                        logger.info("Parsed using NEWS:/EVENTS: markers")
                elif "NEWS" in response_upper and "EVENTS" in response_upper:
                    # Try alternative parsing - look for section headers
                    lines = response_text.split('\n')
                    current_section = None
                    news_lines = []
                    events_lines = []
                    
                    for line in lines:
                        line_upper = line.upper().strip()
                        if 'NEWS' in line_upper and ('PARAGRAPH' in line_upper or ':' in line):
                            current_section = 'news'
                            continue
                        elif 'EVENTS' in line_upper and ('PARAGRAPH' in line_upper or ':' in line):
                            current_section = 'events'
                            continue
                        elif current_section == 'news' and line.strip() and not line.strip().startswith('#'):
                            news_lines.append(line.strip())
                        elif current_section == 'events' and line.strip() and not line.strip().startswith('#'):
                            events_lines.append(line.strip())
                    
                    news_paragraph = ' '.join(news_lines).strip()
                    events_paragraph = ' '.join(events_lines).strip()
                    logger.info(f"Parsed using section headers - news: {len(news_paragraph)} chars, events: {len(events_paragraph)} chars")
                else:
                    # If no clear markers, try to intelligently split
                    # Look for paragraph breaks (double newlines or periods followed by space and capital)
                    logger.warning("No clear NEWS/EVENTS markers found, attempting intelligent split")
                    
                    if news_items and events_items:
                        # Try to find a natural break point
                        # Look for sentence endings followed by what might be a new paragraph
                        sentences = []
                        current_sentence = ""
                        for char in response_text:
                            current_sentence += char
                            if char in '.!?' and len(current_sentence.strip()) > 20:
                                sentences.append(current_sentence.strip())
                                current_sentence = ""
                        if current_sentence.strip():
                            sentences.append(current_sentence.strip())
                        
                        if len(sentences) >= 4:
                            # Split roughly in half, but try to keep paragraphs together
                            mid_point = len(sentences) // 2
                            news_paragraph = ' '.join(sentences[:mid_point])
                            events_paragraph = ' '.join(sentences[mid_point:])
                            logger.info("Split response into two paragraphs by sentence count")
                        else:
                            # Just use the whole response for news if we can't split well
                            news_paragraph = response_text
                            events_paragraph = ""
                            logger.warning("Could not split response, using all as news")
                    elif news_items:
                        news_paragraph = response_text
                    elif events_items:
                        events_paragraph = response_text
                
                # Clean up paragraphs - remove any remaining markers
                news_paragraph = news_paragraph.replace('NEWS:', '').replace('NEWS', '').strip()
                events_paragraph = events_paragraph.replace('EVENTS:', '').replace('EVENTS', '').strip()
                round_scotland_paragraph = round_scotland_paragraph.replace('ROUND SCOTLAND:', '').replace('ROUNDSCOTLAND:', '').replace('ROUND SCOTLAND', '').strip()
                
                # Remove leading/trailing quotes or colons
                news_paragraph = news_paragraph.lstrip(':').strip('"').strip("'").strip()
                events_paragraph = events_paragraph.lstrip(':').strip('"').strip("'").strip()
                round_scotland_paragraph = round_scotland_paragraph.lstrip(':').strip('"').strip("'").strip()
            
            # Log what we parsed
            logger.info(f"Parsed news_paragraph length: {len(news_paragraph)}, events_paragraph length: {len(events_paragraph)}, round_scotland_paragraph length: {len(round_scotland_paragraph)}")
            
            # Validate that we got actual content
            if not news_paragraph and news_items:
                logger.error("News paragraph is empty after LLM call")
                return jsonify({
                    'success': False,
                    'error': 'LLM failed to generate news paragraph. Please try again.',
                    'result': None
                }), 500
            if not events_paragraph and events_items:
                logger.error("Events paragraph is empty after LLM call")
                return jsonify({
                    'success': False,
                    'error': 'LLM failed to generate events paragraph. Please try again.',
                    'result': None
                }), 500
            if not round_scotland_paragraph and round_scotland_items:
                logger.warning("Round Scotland paragraph is empty after LLM call, but continuing")
            
            # Save to block payload
            payload['news_paragraph'] = news_paragraph
            payload['events_paragraph'] = events_paragraph
            if round_scotland_paragraph:
                payload['round_scotland_paragraph'] = round_scotland_paragraph
            payload['compiled_at'] = datetime.now().isoformat()
            payload['manual_override'] = False
            
            update_block_payload(block_id=block_id, payload=payload)
            
            result = {
                'news_paragraph': news_paragraph,
                'events_paragraph': events_paragraph
            }
            if round_scotland_paragraph:
                result['round_scotland_paragraph'] = round_scotland_paragraph
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as llm_error:
            logger.error(f"LLM error in compile_snapshot: {llm_error}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'LLM generation failed: {str(llm_error)}. Please try again.',
                'result': None
            }), 500
            
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error compiling snapshot: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-round-scotland', methods=['GET'])
def generate_round_scotland_component(issue_id: int, block_id: int):
    """Generate Round Scotland component for snapshot block - returns weekly highlights items."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload, get_issue
        from newsletter.services.weekly_highlights_selection import select_weekly_highlights
        from config.database import db_manager
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Check if weekly_highlights exists for this issue
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM weekly_highlights WHERE issue_id = %s
                """, (issue_id,))
                row = cur.fetchone()
                highlights_id = row[0] if row else None
        
        # Create highlights if missing
        if not highlights_id:
            logger.info(f"Creating weekly highlights for issue {issue_id}")
            selection_result = select_weekly_highlights(issue_id, target_week)
            if not selection_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': selection_result.get('error', 'Failed to create highlights'),
                    'items': []
                })
            highlights_id = selection_result.get('highlights_id')
        
        # Get highlight items
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT whi.id, whi.position, whi.title_internal, whi.summary_newsletter,
                           whi.location_label, whi.source_label, whi.permalink,
                           nsi.title, nsi.url, nsi.source_name, nsi.llm_quirky_score
                    FROM weekly_highlights_items whi
                    JOIN newsletter_source_item nsi ON whi.article_id = nsi.id
                    WHERE whi.weekly_highlights_id = %s
                    ORDER BY whi.position
                """, (highlights_id,))
                rows = cur.fetchall() or []
        
        # Format items
        formatted_items = []
        for row in rows:
            formatted_items.append({
                'id': row[0],
                'position': row[1],
                'title_internal': row[2] or row[7],  # Use generated or fallback to article title
                'summary_newsletter': row[3] or '',
                'location': row[4] or '',
                'source_label': row[5] or row[9],  # Use generated or fallback to source_name
                'url': row[6] or row[8],
                'quirky_score': row[10] or 0
            })
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        payload['round_scotland_items'] = formatted_items
        update_block_payload(block_id=block_id, payload=payload)
        
        return jsonify({
            'success': True,
            'items': formatted_items
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating Round Scotland component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500


