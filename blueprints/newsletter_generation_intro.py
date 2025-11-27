"""Newsletter Generation Intro Routes."""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from typing import List, Dict, Any
import os, sys

# Ensure the newsletter package (under blog-core/newsletter) is importable
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blog-core'))

# Import common dependencies
from newsletter.db.queries_issue import get_issue
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('newsletter_generation_intro', __name__)


@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-weather', methods=['GET'])
def generate_weather_component(issue_id: int, block_id: int):
    """Generate weather component for intro block."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.services.weather_analysis_service import get_weather_for_intro
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        weather_result = get_weather_for_intro(target_week=target_week)
        
        if weather_result:
            return jsonify({
                'success': True,
                'text': weather_result.get('summary_text', ''),
                'source_name': weather_result.get('source_name', ''),
                'url': weather_result.get('url', ''),
                'analysis': weather_result.get('analysis', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No weather data available for this period',
                'text': ''
            })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating weather component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-events', methods=['GET'])
def generate_events_component(issue_id: int, block_id: int):
    """Generate events component for intro block using LLM to create conversational comment."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.services.suggestion_service import generate_suggestions
        from newsletter.services.events_summary_service import get_event_detail
        from blueprints.header.llm_service import LLMService
        import os
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        target_week = issue.get('target_week', '')
        
        # Get top event suggestion
        event_suggestions = generate_suggestions(block_type='intro', target_week=target_week, count=5, skip_validation=True)
        event_items = [s for s in event_suggestions if s.get('category') == 'event']
        
        if not event_items:
            return jsonify({
                'success': False,
                'error': 'No event suggestions available',
                'text': ''
            })
        
        event_item = event_items[0]
        event_id = event_item.get('id')
        
        # Get full event details including description
        event_detail = get_event_detail(event_id) if event_id else None
        
        # Extract event information
        source = event_item.get('source_name', '')
        title = event_item.get('title', '')
        location = event_item.get('location', '')
        url = event_item.get('url', '')
        
        # Get additional details from event_detail or raw_data
        description = ''
        date_text = ''
        if event_detail:
            description = event_detail.get('description', '') or event_detail.get('raw_data', {}).get('description', '')
            date_text = event_detail.get('date_text', '') or event_detail.get('raw_data', {}).get('date_text', '')
        else:
            # Fallback to raw_data from event_item
            raw_data = event_item.get('raw_data', {})
            description = raw_data.get('description', '') or raw_data.get('summary', '')
            date_text = raw_data.get('date_text', '')
        
        # Get event date
        event_date = event_item.get('event_date') or (event_detail.get('event_date') if event_detail else None)
        if event_date:
            if isinstance(event_date, str):
                from dateutil import parser
                try:
                    event_date = parser.parse(event_date)
                except:
                    event_date = None
        
        # Use LLM to generate conversational comment
        llm_service = LLMService()
        
        system_prompt = """You are writing a conversational, chatty comment about a Scottish cultural event for a heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, observational tone - like you're chatting with a friend about something interesting you've discovered.
Focus on what makes this event interesting or notable, not just announcing it.
Keep it to ONE sentence, maximum 30 words.
Write naturally - avoid clichés or repeated phrases. Each comment should be unique based on what's actually interesting about the event."""
        
        # Build user prompt with event details
        event_info_parts = []
        event_info_parts.append(f"EVENT: {title}")
        if location:
            event_info_parts.append(f"LOCATION: {location}")
        if source:
            event_info_parts.append(f"ORGANIZER: {source}")
        if event_date:
            event_info_parts.append(f"DATE: {event_date.strftime('%d %B %Y') if hasattr(event_date, 'strftime') else str(event_date)}")
        if date_text:
            event_info_parts.append(f"DATE TEXT: {date_text}")
        if description:
            # Limit description length for prompt
            desc_preview = description[:500] if len(description) > 500 else description
            event_info_parts.append(f"DESCRIPTION: {desc_preview}")
        
        user_prompt = f"""Write a single conversational sentence about this Scottish cultural event:

{chr(10).join(event_info_parts)}

Write ONE conversational sentence that:
1. Comments on what's interesting or notable about this event
2. Mentions the event naturally (not just "X has announced Y")
3. Highlights something that would appeal to someone interested in Scottish heritage/culture
4. Uses natural, varied language - avoid clichés
5. Sounds like a human observation, not a press release

Think about:
- What makes this event special or interesting?
- What would catch someone's attention?
- What cultural or historical significance does it have?
- What's the human angle or story?

If the description reveals something interesting (historical context, unique features, cultural significance), mention that naturally.

Your response should be ONLY the sentence, nothing else."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error generating events component: {result['error']}")
                # Fallback to simple format
                if location:
                    text = f"Meanwhile, {source} has announced {title} in {location}."
                else:
                    text = f"Meanwhile, {source} has announced {title}."
            else:
                text = result.get('content', '').strip()
                # Clean up the response
                text = text.strip('"\'')
                text = text.strip()
                # Ensure it ends with proper punctuation
                if text and not text[-1] in '.!?':
                    text += '.'
                
                # Fallback if LLM returned empty
                if not text:
                    if location:
                        text = f"Meanwhile, {source} has announced {title} in {location}."
                    else:
                        text = f"Meanwhile, {source} has announced {title}."
        
        except Exception as e:
            logger.error(f"Error calling LLM for events component: {e}", exc_info=True)
            # Fallback to simple format
            if location:
                text = f"Meanwhile, {source} has announced {title} in {location}."
            else:
                text = f"Meanwhile, {source} has announced {title}."
        
        return jsonify({
            'success': True,
            'text': text,
            'source_name': source,
            'title': title,
            'location': location,
            'url': url,
            'suggestion_id': event_id
        })
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating events component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/generate-theme', methods=['GET'])
def generate_theme_component(issue_id: int, block_id: int):
    """Generate theme component for intro block using LLM to create conversational comment."""
    try:
        from newsletter.db.queries_issue import get_block
        from newsletter.selectors.theme import parse_target_week, get_theme_by_id
        from blueprints.header.llm_service import LLMService
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        issue = get_issue(issue_id=issue_id)
        if not issue:
            return jsonify({'error': 'Issue not found'}), 404
        
        # Get theme from issue
        theme_id = issue.get('theme_id')
        if not theme_id:
            return jsonify({
                'success': False,
                'error': 'No theme selected for this issue',
                'text': ''
            })
        
        theme = get_theme_by_id(theme_id)
        if not theme:
            return jsonify({
                'success': False,
                'error': 'Theme not found',
                'text': ''
            })
        
        # Extract theme information
        theme_title = theme.get('idea_title', '')
        idea_description = theme.get('idea_description', '')
        seasonal_context = theme.get('seasonal_context', '')
        content_type = theme.get('content_type', '')
        tags = theme.get('tags', [])
        week_number = theme.get('week_number', '')
        
        # Use LLM to generate conversational comment
        llm_service = LLMService()
        
        system_prompt = """You are writing a conversational, chatty comment about a weekly theme for a Scottish heritage newsletter.
Your audience is primarily US-Scots diaspora - people of Scottish descent living abroad who maintain an interest in Scotland.
Write in a warm, friendly, observational tone - like you're chatting with a friend about what you'll be exploring this week.
Focus on what makes this theme interesting or relevant, not just announcing it.
Keep it to ONE sentence, maximum 30 words.
Write naturally - avoid clichés or repeated phrases. Each comment should be unique based on what's actually interesting about the theme."""
        
        # Build user prompt with theme details
        theme_info_parts = []
        theme_info_parts.append(f"THEME: {theme_title}")
        if seasonal_context:
            theme_info_parts.append(f"SEASONAL CONTEXT: {seasonal_context}")
        if idea_description:
            # Limit description length for prompt
            desc_preview = idea_description[:500] if len(idea_description) > 500 else idea_description
            theme_info_parts.append(f"DESCRIPTION: {desc_preview}")
        if content_type:
            theme_info_parts.append(f"CONTENT TYPE: {content_type}")
        if tags:
            tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)
            theme_info_parts.append(f"TAGS: {tags_str}")
        if week_number:
            theme_info_parts.append(f"WEEK: {week_number}")
        
        user_prompt = f"""Write a single conversational sentence about this week's theme for the newsletter:

{chr(10).join(theme_info_parts)}

Write ONE conversational sentence that:
1. Comments on what's interesting or relevant about this theme
2. Mentions the theme naturally (not just "we're exploring X")
3. Highlights why this theme matters for someone interested in Scottish heritage/culture
4. Uses natural, varied language - avoid clichés
5. Sounds like a human observation, not a formal announcement

Think about:
- What makes this theme special or relevant?
- What would catch someone's attention?
- What cultural or historical significance does it have?
- Why is this theme timely or interesting?
- What's the human angle or story?

If the description reveals something interesting (historical context, cultural significance, seasonal relevance), mention that naturally.

Your response should be ONLY the sentence, nothing else."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error generating theme component: {result['error']}")
                # Fallback to simple format
                if seasonal_context:
                    text = f"This week we're exploring {theme_title.lower()}, {seasonal_context.lower()}."
                else:
                    text = f"This week we're exploring {theme_title.lower()}."
            else:
                text = result.get('content', '').strip()
                # Clean up the response
                text = text.strip('"\'')
                text = text.strip()
                # Ensure it ends with proper punctuation
                if text and not text[-1] in '.!?':
                    text += '.'
                
                # Fallback if LLM returned empty
                if not text:
                    if seasonal_context:
                        text = f"This week we're exploring {theme_title.lower()}, {seasonal_context.lower()}."
                    else:
                        text = f"This week we're exploring {theme_title.lower()}."
        
        except Exception as e:
            logger.error(f"Error calling LLM for theme component: {e}", exc_info=True)
            # Fallback to simple format
            if seasonal_context:
                text = f"This week we're exploring {theme_title.lower()}, {seasonal_context.lower()}."
            else:
                text = f"This week we're exploring {theme_title.lower()}."
        
        return jsonify({
            'success': True,
            'text': text,
            'theme_title': theme_title,
            'seasonal_context': seasonal_context,
            'theme_id': theme_id
        })
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error generating theme component: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500



@bp.route('/newsletter/issue/<int:issue_id>/block/<int:block_id>/compile-intro', methods=['POST'])
def compile_intro(issue_id: int, block_id: int):
    """Compile weather, events, and theme into final intro paragraph using LLM."""
    try:
        from newsletter.db.queries_issue import get_block, update_block_payload
        from blueprints.header.llm_service import LLMService
        import logging
        logger = logging.getLogger(__name__)
        
        block = get_block(block_id=block_id)
        if not block:
            return jsonify({'error': 'Block not found'}), 404
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        weather_text = data.get('weather_text', '').strip()
        events_text = data.get('events_text', '').strip()
        theme_text = data.get('theme_text', '').strip()
        
        # Filter out placeholder/loading messages
        def is_valid_component(text):
            if not text:
                return False
            # Filter out placeholder messages
            invalid_phrases = ['Click "Generate"', 'Generating', 'Error:', 'No content yet']
            return not any(phrase in text for phrase in invalid_phrases)
        
        valid_components = []
        if is_valid_component(weather_text):
            valid_components.append(('weather', weather_text))
        if is_valid_component(events_text):
            valid_components.append(('events', events_text))
        if is_valid_component(theme_text):
            valid_components.append(('theme', theme_text))
        
        if not valid_components:
            return jsonify({
                'success': False,
                'error': 'No valid components provided to compile',
                'text': ''
            })
        
        # Use LLM to create coherent paragraph
        llm_service = LLMService()
        
        system_prompt = """You are writing the opening of a Scottish heritage newsletter for the US-Scots diaspora.

Write in a warm, friendly, welcoming tone.

Use all provided information to craft a natural, conversational introduction.

Produce exactly three paragraphs using HTML <p> tags. Each paragraph must contain 2–4 sentences.

Weave the information into flowing prose rather than repeating the original wording.

Your output MUST be in this exact format:
<p>[First paragraph text]</p>
<p>[Second paragraph text]</p>
<p>[Third paragraph text]</p>"""
        
        # Build user prompt with all components
        components_info = []
        for comp_type, comp_text in valid_components:
            components_info.append(f"{comp_type.upper()}: {comp_text}")
        
        user_prompt = f"""You have three pieces of information about this week's newsletter:

{chr(10).join(components_info)}

Your task:
1. Consider all three elements as information (not as sentences to repeat).
2. Decide the best sequencing (what opens the conversation, what closes).
3. Write exactly three paragraphs using HTML <p> tags, each 2–4 sentences, welcoming readers and smoothly weaving the information together into a friendly introduction.

Your response MUST be in this exact format:
<p>[First paragraph text]</p>
<p>[Second paragraph text]</p>
<p>[Third paragraph text]</p>

Output only the HTML paragraphs, nothing else."""
        
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # Use Ollama by default (local, fast)
            result = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages)
            
            if 'error' in result:
                logger.error(f"LLM error compiling intro: {result['error']}")
                # Fallback: simple concatenation
                compiled_text = ' '.join([text for _, text in valid_components])
            else:
                compiled_text = result.get('content', '').strip()
                
                # Clean up the response - remove any commentary or notes
                compiled_text = compiled_text.strip('"\'')
                
                # Remove any parenthetical commentary or notes
                import re
                # Remove patterns like "(Note: ...)" or "(I've ...)" etc.
                compiled_text = re.sub(r'\(Note:.*?\)', '', compiled_text, flags=re.IGNORECASE | re.DOTALL)
                compiled_text = re.sub(r'\(I\'ve.*?\)', '', compiled_text, flags=re.IGNORECASE | re.DOTALL)
                compiled_text = re.sub(r'\(Let me.*?\)', '', compiled_text, flags=re.IGNORECASE | re.DOTALL)
                compiled_text = re.sub(r'\(.*?reorganized.*?\)', '', compiled_text, flags=re.IGNORECASE | re.DOTALL)
                
                # Remove any lines that start with "Note:" or similar meta-commentary
                lines = compiled_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    # Skip lines that are clearly commentary
                    if (line_stripped.lower().startswith('note:') or 
                        line_stripped.lower().startswith('(note:') or
                        line_stripped.lower().startswith('i\'ve') or
                        line_stripped.lower().startswith('let me') or
                        'reorganized' in line_stripped.lower() and '(' in line_stripped):
                        continue
                    cleaned_lines.append(line)
                compiled_text = '\n'.join(cleaned_lines).strip()
                
                # Remove "CAT " prefix if LLM included it (from old prompt)
                if compiled_text.startswith('CAT '):
                    compiled_text = compiled_text[4:].lstrip()
                
                # NEW: Parse HTML <p> tags first
                p_tag_pattern = r'<p[^>]*>(.*?)</p>'
                p_matches = re.findall(p_tag_pattern, compiled_text, re.IGNORECASE | re.DOTALL)
                
                if len(p_matches) >= 2:
                    # Successfully extracted paragraphs from HTML tags
                    paragraphs = [p.strip() for p in p_matches if p.strip()]
                    compiled_text = '\n\n'.join(paragraphs)
                    logger.info(f"Extracted {len(paragraphs)} paragraphs from HTML tags")
                else:
                    # Fall back to parsing paragraphs - look for multiple paragraphs separated by blank lines
                    paragraphs = [p.strip() for p in compiled_text.split('\n\n') if p.strip()]
                
                # Also check for single newline splits (some LLMs use single \n)
                if len(paragraphs) == 1:
                    # Try splitting on single newlines first
                    single_line_paras = [p.strip() for p in compiled_text.split('\n') if p.strip() and len(p.strip()) > 30]
                    if len(single_line_paras) >= 2:
                        paragraphs = single_line_paras
                
                # If we have multiple paragraphs, use them all
                if len(paragraphs) >= 2:
                    compiled_text = '\n\n'.join(paragraphs)  # Use all paragraphs
                else:
                    # Force split single paragraph
                    text = paragraphs[0] if paragraphs else compiled_text
                    
                    # Find all sentence boundaries (period/exclamation/question + space + capital)
                    split_points = []
                    for i in range(len(text) - 2):
                        if text[i] in '.!?' and i+1 < len(text) and text[i+1] == ' ':
                            if i+2 < len(text) and text[i+2].isupper():
                                # Additional check: make sure it's not an abbreviation
                                if i > 0 and text[i-1].isalpha():
                                    split_points.append(i+1)
                    
                    # If we found split points, use the middle one
                    if len(split_points) >= 1:
                        split_idx = split_points[len(split_points) // 2]
                        first_para = text[:split_idx].strip()
                        second_para = text[split_idx:].strip()
                        if len(first_para) > 30 and len(second_para) > 30:
                            compiled_text = f"{first_para}\n\n{second_para}"
                    
                    # If still not split, force split at roughly 40% of the way through
                    if '\n\n' not in compiled_text:
                        target_pos = int(len(text) * 0.4)
                        best_split = None
                        best_distance = float('inf')
                        
                        for i in range(max(0, target_pos - 150), min(len(text), target_pos + 150)):
                            if text[i] in '.!?' and i+1 < len(text) and text[i+1] == ' ':
                                if i+2 < len(text) and text[i+2].isupper():
                                    distance = abs(i - target_pos)
                                    if distance < best_distance:
                                        best_distance = distance
                                        best_split = i + 1
                        
                        if best_split:
                            first_para = text[:best_split].strip()
                            second_para = text[best_split:].strip()
                            if len(first_para) > 30 and len(second_para) > 30:
                                compiled_text = f"{first_para}\n\n{second_para}"
                    
                    # Final check: if we still have only one paragraph, force split at middle
                    if '\n\n' not in compiled_text:
                        mid_point = len(text) // 2
                        for i in range(mid_point, max(0, mid_point - 100), -1):
                            if text[i] in '.!?' and i+1 < len(text):
                                first_para = text[:i+1].strip()
                                second_para = text[i+1:].strip()
                                if len(first_para) > 20 and len(second_para) > 20:
                                    compiled_text = f"{first_para}\n\n{second_para}"
                                    break
                        
                        # Absolute last resort: split at space near middle
                        if '\n\n' not in compiled_text:
                            for i in range(mid_point, max(0, mid_point - 50), -1):
                                if text[i] == ' ':
                                    first_para = text[:i].strip()
                                    second_para = text[i:].strip()
                                    compiled_text = f"{first_para}\n\n{second_para}"
                                    break
                
                # Final validation: ensure we have at least 2 paragraphs
                final_paragraphs = [p.strip() for p in compiled_text.split('\n\n') if p.strip()]
                if len(final_paragraphs) < 2:
                    logger.warning(f"Failed to split into 2 paragraphs, got {len(final_paragraphs)}. Original: {compiled_text[:100]}...")
                    # One more attempt: split on any sentence boundary
                    if len(final_paragraphs) == 1:
                        text = final_paragraphs[0]
                        # Find first sentence ending after 30% of text
                        min_pos = int(len(text) * 0.3)
                        for i in range(min_pos, len(text) - 1):
                            if text[i] in '.!?' and text[i+1] == ' ':
                                first_para = text[:i+1].strip()
                                second_para = text[i+1:].strip()
                                compiled_text = f"{first_para}\n\n{second_para}"
                                break
                compiled_text = compiled_text.strip()
                
                # Fallback if LLM returned empty
                if not compiled_text:
                    compiled_text = ' '.join([text for _, text in valid_components])
        
        except Exception as e:
            logger.error(f"Error calling LLM for compile intro: {e}", exc_info=True)
            # Fallback: simple concatenation
            compiled_text = ' '.join([text for _, text in valid_components])
        
        # Save to block payload
        payload = block.get('payload_json', {}) or {}
        
        # Remove "CAT " prefix if LLM included it (from old prompt)
        if compiled_text.startswith('CAT '):
            compiled_text = compiled_text[4:].lstrip()
        
        # Ensure no leading whitespace
        compiled_text = compiled_text.lstrip()
        
        payload['text'] = compiled_text
        payload['weather_text'] = weather_text
        payload['events_text'] = events_text
        payload['theme_text'] = theme_text
        payload['manual_override'] = False
        
        update_block_payload(block_id=block_id, payload=payload)
        
        # Remove "CAT " prefix if present in response
        response_text = compiled_text
        if response_text.startswith('CAT '):
            response_text = response_text[4:].lstrip()
        
        return jsonify({
            'success': True,
            'text': response_text
        })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error compiling intro: {e}", exc_info=True)
        return jsonify({'error': str(e), 'success': False}), 500
