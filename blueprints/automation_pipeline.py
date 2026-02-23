"""
Pipeline Status and Data API Endpoints
"""

from flask import Blueprint, jsonify, request
import json
from datetime import datetime, timedelta, date, timezone
from config.database import db_manager
from utils.substage_config import get_substages_for_post_type, is_substage_valid_for_post_type
from config.output_channel_stages import (
    get_stages_for_output,
    get_substages_for_output,
    get_all_stages_for_output
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('automation_pipeline', __name__)

@bp.route('/pipeline-status/<int:post_id>', methods=['GET'])
def get_pipeline_status(post_id):
    """Get current pipeline state for a post, optionally filtered by output channel"""
    try:
        # Get output channel from query parameter (defaults to 'blog')
        output_channel = request.args.get('output', 'blog').lower()
        
        # Validate output channel
        valid_channels = ['blog', 'facebook', 'instagram', 'twitter', 'newsletter']
        if output_channel not in valid_channels:
            output_channel = 'blog'
        with db_manager.get_cursor() as cursor:
            # Get post basic info with timestamps
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.updated_at,
                       p.theme_id, p.content_type_id, p.format_id,
                       p.summary, p.subtitle, p.header_image_id, 
                       p.header_image_caption, p.header_image_alt_text,
                       p.meta_title, p.meta_description, p.meta_tags, p.slug,
                       p.profile_product_id, p.cross_promotion_product_id,
                       p.recipe_id, p.profile_category_id, p.generated_source_type,
                       pd.sections, pd.topic_allocation, pd.section_structure,
                       pd.idea_scope, pd.expanded_idea,
                       pd.structure_design_at, pd.allocation_completed_at,
                       pd.refinement_completed_at, pd.updated_at as sections_updated_at,
                       pd.updated_at as authoring_updated_at,
                       pd.updated_at as image_concepts_updated_at,
                       pd.updated_at as planning_updated_at,
                       p.created_at as post_updated_at
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
            # Determine post_type from post fields (same logic as get_post_type())
            if post.get('recipe_id') is not None:
                post_type = 'recipe'
            elif post.get('profile_category_id') is not None:
                post_type = 'profile'
            elif post.get('generated_source_type') is not None:
                post_type = 'generated'
            else:
                post_type = 'themed'
            
            # Get content format for this (post_type, output_channel) combination
            content_format = None
            try:
                from utils.channel_assignment import get_content_format
                content_format = get_content_format(post_type, output_channel)
            except Exception as e:
                logger.warning(f"Could not resolve content format for {post_type}/{output_channel}: {e}")
            
            # Get section completion status (limit to section_order <= 7)
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted,
                       SUM(CASE WHEN image_concepts IS NOT NULL AND image_concepts != '' THEN 1 ELSE 0 END) as image_concepts_count,
                       SUM(CASE WHEN image_prompts IS NOT NULL AND image_prompts != '' THEN 1 ELSE 0 END) as image_prompts_count,
                       SUM(CASE WHEN image_captions IS NOT NULL AND image_captions != '' THEN 1 ELSE 0 END) as image_captions_count,
                       SUM(CASE WHEN image_filename IS NOT NULL AND image_filename != '' THEN 1 ELSE 0 END) as image_generated_count,
                       MAX(image_generated_at) as last_image_generated_at
                FROM post_section
                WHERE post_id = %s AND section_order <= 7
            """, (post_id,))
            
            section_stats = cursor.fetchone()
            
            # Check image optimization completion
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ps.id) as total_sections,
                    COUNT(DISTINCT pi.section_id) as optimized_sections,
                    MAX(pi.created_at) as last_optimized_at
                FROM post_section ps
                LEFT JOIN post_images pi ON ps.id = pi.section_id AND pi.image_type = 'section_optimized'
                WHERE ps.post_id = %s AND ps.section_order <= 7
            """, (post_id,))
            
            optimization_stats = cursor.fetchone()
            
            # Check calendar assignment
            # New system: posts are linked to calendar items via idea_seed (themes/weekly content) or recipe_id (recipes)
            # Check if post has idea_seed (indicates calendar item link) or recipe_id
            is_calendar_assigned = bool(
                post.get('idea_seed') or 
                post.get('recipe_id') is not None or
                post.get('profile_category_id') is not None
            )
            
            # Check image concepts completion from JSON data
            image_concepts_complete = False
            image_prompts_complete = False
            image_captions_complete = False
            sections_with_concepts = 0
            sections_with_prompts = 0
            sections_with_captions = 0
            total_sections = 0
            
            if post['sections']:
                try:
                    sections_data = json.loads(post['sections']) if isinstance(post['sections'], str) else post['sections']
                    if isinstance(sections_data, dict) and 'sections' in sections_data:
                        sections_list = sections_data['sections']
                    elif isinstance(sections_data, list):
                        sections_list = sections_data
                    else:
                        sections_list = []
                    
                    # Check completion for all image-related fields
                    total_sections = len(sections_list)
                    sections_with_concepts = sum(1 for section in sections_list if section.get('image_concepts'))
                    sections_with_prompts = sum(1 for section in sections_list if section.get('image_prompts'))
                    sections_with_captions = sum(1 for section in sections_list if section.get('image_captions'))
                    
                    # Also check post_section table for integer-based sections
                    if section_stats and section_stats['total'] > 0:
                        # Use the higher count from either source
                        total_sections = max(total_sections, section_stats['total'])
                        sections_with_concepts = max(sections_with_concepts, section_stats['image_concepts_count'])
                        sections_with_prompts = max(sections_with_prompts, section_stats['image_prompts_count'])
                        sections_with_captions = max(sections_with_captions, section_stats['image_captions_count'])
                    
                    image_concepts_complete = total_sections > 0 and sections_with_concepts == total_sections
                    image_prompts_complete = total_sections > 0 and sections_with_prompts == total_sections
                    image_captions_complete = total_sections > 0 and sections_with_captions == total_sections
                except (json.JSONDecodeError, TypeError):
                    image_concepts_complete = False
                    image_prompts_complete = False
                    image_captions_complete = False
            
            # Calculate completion statuses for each substage
            
            # Planning substages
            ideas_complete = bool(post.get('expanded_idea') and post['expanded_idea'].strip() != '')
            taxonomy_complete = bool(
                post.get('theme_id') is not None and 
                post.get('content_type_id') is not None and 
                post.get('format_id') is not None
            )
            topic_brainstorming_complete = bool(post.get('idea_scope') and post['idea_scope'].strip() != '')
            section_structure_complete = bool(post.get('section_structure'))
            topic_allocation_complete = bool(post.get('topic_allocation'))
            section_titling_complete = bool(post.get('sections') and post['sections'].strip() != '')
            
            # Planning stage complete if all planning substages are complete
            planning_complete = bool(
                ideas_complete and taxonomy_complete and 
                topic_brainstorming_complete and section_structure_complete and
                topic_allocation_complete and section_titling_complete
            )
            
            # Authoring substages
            authoring_progress = 0
            if section_stats and section_stats['total'] > 0:
                authoring_progress = int((section_stats['drafted'] / section_stats['total']) * 100)
            
            author_first_drafts_complete = (authoring_progress == 100 and section_stats['total'] > 0)
            
            # Image generation and optimization
            image_generation_complete = False
            image_generation_progress = 0
            if section_stats and section_stats['total'] > 0:
                image_generation_progress = int((section_stats['image_generated_count'] / section_stats['total']) * 100)
                image_generation_complete = (section_stats['image_generated_count'] == section_stats['total'])
            
            image_optimization_complete = False
            image_optimization_progress = 0
            if optimization_stats and optimization_stats['total_sections'] > 0:
                image_optimization_progress = int((optimization_stats['optimized_sections'] / optimization_stats['total_sections']) * 100)
                image_optimization_complete = (optimization_stats['optimized_sections'] == optimization_stats['total_sections'])
            
            # Header substages
            title_summary_complete = bool(
                post.get('title') and post['title'].strip() != '' and
                post.get('summary') and post['summary'].strip() != ''
            )
            
            header_image_complete = bool(post.get('header_image_id') is not None)
            
            seo_meta_complete = bool(
                post.get('meta_title') and post['meta_title'].strip() != '' and
                post.get('meta_description') and post['meta_description'].strip() != '' and
                post.get('slug') and post['slug'].strip() != ''
            )
            
            product_match_complete = bool(
                post.get('profile_product_id') is not None or 
                post.get('cross_promotion_product_id') is not None
            )
            
            # Final review: all header substages complete
            final_review_complete = bool(
                title_summary_complete and header_image_complete and 
                seo_meta_complete
            )
            
            # Determine overall progress
            overall_progress = 0
            if planning_complete:
                overall_progress += 40
            overall_progress += int(authoring_progress * 0.6)
            
            # Extract timestamps
            ideas_completed_at = post.get('planning_updated_at') if ideas_complete and post.get('planning_updated_at') else None
            taxonomy_completed_at = post.get('updated_at') if taxonomy_complete and post.get('updated_at') else None
            
            topic_brainstorming_at = None
            if post.get('idea_scope'):
                try:
                    idea_scope_data = json.loads(post['idea_scope']) if isinstance(post['idea_scope'], str) else post['idea_scope']
                    if isinstance(idea_scope_data, dict) and 'generated_at' in idea_scope_data:
                        topic_brainstorming_at = datetime.fromisoformat(idea_scope_data['generated_at'])
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
            
            image_generation_completed_at = section_stats.get('last_image_generated_at') if image_generation_complete and section_stats and section_stats.get('last_image_generated_at') else None
            image_optimization_completed_at = optimization_stats.get('last_optimized_at') if image_optimization_complete and optimization_stats and optimization_stats.get('last_optimized_at') else None
            
            header_completed_at = post.get('updated_at') if final_review_complete and post.get('updated_at') else None
            
            # Build all substage data (before filtering by post_type)
            all_substages_data = {
                "calendar": {
                    "calendar_view": {
                        "status": "complete",
                        "completed_at": None,
                        "progress": 100
                    },
                    "idea_generation": {
                        "status": "complete" if is_calendar_assigned else "pending",
                        "completed_at": None,
                        "progress": 100 if is_calendar_assigned else 0
                    }
                },
                "planning": {
                    "ideas": {
                        "status": "complete" if ideas_complete else "pending",
                        "completed_at": ideas_completed_at.isoformat() if ideas_completed_at else None,
                        "progress": 100 if ideas_complete else 0
                    },
                    "taxonomy": {
                        "status": "complete" if taxonomy_complete else "pending",
                        "completed_at": taxonomy_completed_at.isoformat() if taxonomy_completed_at else None,
                        "progress": 100 if taxonomy_complete else 0
                    },
                    "topic_brainstorming": {
                        "status": "complete" if topic_brainstorming_complete else "pending",
                        "completed_at": topic_brainstorming_at.isoformat() if topic_brainstorming_at else None,
                        "progress": 100 if topic_brainstorming_complete else 0
                    },
                    "section_structure": {
                        "status": "complete" if section_structure_complete else "pending",
                        "completed_at": post.get('structure_design_at').isoformat() if post.get('structure_design_at') else None,
                        "progress": 100 if section_structure_complete else 0
                    },
                    "topic_allocation": {
                        "status": "complete" if topic_allocation_complete else "pending",
                        "completed_at": post.get('allocation_completed_at').isoformat() if post.get('allocation_completed_at') else None,
                        "progress": 100 if topic_allocation_complete else 0
                    },
                    "section_titling": {
                        "status": "complete" if section_titling_complete else "pending",
                        "completed_at": post.get('sections_updated_at').isoformat() if post.get('sections_updated_at') else None,
                        "progress": 100 if section_titling_complete else 0
                    },
                    "product_data_review": {
                        "status": "pending",  # TODO: Add completion logic for generated posts
                        "completed_at": None,
                        "progress": 0
                    },
                    "section_content_mapping": {
                        "status": "pending",  # TODO: Add completion logic for generated posts
                        "completed_at": None,
                        "progress": 0
                    }
                },
                "authoring": {
                    "author_first_drafts": {
                        "status": "complete" if author_first_drafts_complete else ("in_progress" if authoring_progress > 0 else "pending"),
                        "completed_at": post['updated_at'].isoformat() if author_first_drafts_complete and post['updated_at'] else None,
                        "progress": authoring_progress
                    },
                    "image_concepts": {
                        "status": "complete" if image_concepts_complete else ("in_progress" if sections_with_concepts > 0 else "pending"),
                        "completed_at": post.get('authoring_updated_at').isoformat() if image_concepts_complete and post.get('authoring_updated_at') else None,
                        "progress": int((sections_with_concepts / total_sections * 100)) if total_sections > 0 else 0
                    },
                    "image_prompts": {
                        "status": "complete" if image_prompts_complete else ("in_progress" if sections_with_prompts > 0 else "pending"),
                        "completed_at": post.get('sections_updated_at').isoformat() if image_prompts_complete and post.get('sections_updated_at') else None,
                        "progress": int((sections_with_prompts / total_sections * 100)) if total_sections > 0 else 0
                    },
                    "image_captions": {
                        "status": "complete" if image_captions_complete else ("in_progress" if sections_with_captions > 0 else "pending"),
                        "completed_at": post.get('post_updated_at').isoformat() if image_captions_complete and post.get('post_updated_at') else None,
                        "progress": int((sections_with_captions / total_sections * 100)) if total_sections > 0 else 0
                    },
                    "recipe_image_style_prompt": {
                        "status": "pending",  # TODO: Add completion logic for recipe posts
                        "completed_at": None,
                        "progress": 0
                    }
                },
                "imaging": {
                    "image_generation": {
                        "status": "complete" if image_generation_complete else ("in_progress" if image_generation_progress > 0 else "pending"),
                        "completed_at": image_generation_completed_at.isoformat() if image_generation_completed_at else None,
                        "progress": image_generation_progress
                    },
                    "optimise": {
                        "status": "complete" if image_optimization_complete else ("in_progress" if image_optimization_progress > 0 else "pending"),
                        "completed_at": image_optimization_completed_at.isoformat() if image_optimization_completed_at else None,
                        "progress": image_optimization_progress
                    }
                },
                "header": {
                    "title_summary": {
                        "status": "complete" if title_summary_complete else "pending",
                        "completed_at": post.get('updated_at').isoformat() if title_summary_complete and post.get('updated_at') else None,
                        "progress": 100 if title_summary_complete else 0
                    },
                    "header_image": {
                        "status": "complete" if header_image_complete else "pending",
                        "completed_at": post.get('updated_at').isoformat() if header_image_complete and post.get('updated_at') else None,
                        "progress": 100 if header_image_complete else 0
                    },
                    "seo_meta": {
                        "status": "complete" if seo_meta_complete else "pending",
                        "completed_at": post.get('updated_at').isoformat() if seo_meta_complete and post.get('updated_at') else None,
                        "progress": 100 if seo_meta_complete else 0
                    },
                    "product_match": {
                        "status": "complete" if product_match_complete else "pending",
                        "completed_at": post.get('updated_at').isoformat() if product_match_complete and post.get('updated_at') else None,
                        "progress": 100 if product_match_complete else 0
                    },
                    "final_review": {
                        "status": "complete" if final_review_complete else "pending",
                        "completed_at": header_completed_at.isoformat() if header_completed_at else None,
                        "progress": 100 if final_review_complete else 0
                    }
                }
            }
            
            # Get output channel configuration
            # Get content format and resolve stages
            output_config = get_stages_for_output(post_type, output_channel, content_format)
            
            # Determine which stages and substages to include
            if output_config.get('use_post_type_config'):
                # Use post_type_substages (blog output)
                valid_stages = get_substages_for_post_type(post_type)
                # Filter by post_type as before
                filtered_stages = {}
                for stage_name, substages_data in all_substages_data.items():
                    if stage_name not in valid_stages:
                        continue
                    valid_substages = get_substages_for_post_type(post_type, stage_name)
                    filtered_substages = {
                        key: data for key, data in substages_data.items()
                        if key in valid_substages
                    }
                    if filtered_substages:
                        stage_status = "complete" if all(s.get("status") == "complete" for s in filtered_substages.values()) else ("in_progress" if any(s.get("status") == "in_progress" for s in filtered_substages.values()) else "pending")
                        stage_progress = int(sum(s.get("progress", 0) for s in filtered_substages.values()) / len(filtered_substages)) if filtered_substages else 0
                        filtered_stages[stage_name] = {
                            "status": stage_status,
                            "progress": stage_progress,
                            "substages": filtered_substages
                        }
            else:
                # Use channel-specific stages
                channel_stages = output_config.get('stages', [])
                channel_substages = output_config.get('substages', {})
                
                filtered_stages = {}
                for stage_name in channel_stages:
                    # Get valid substages for this channel and stage
                    valid_substages = channel_substages.get(stage_name, [])
                    
                    # Filter substages from all_substages_data
                    # Note: For channel-specific stages like 'syndication', 'publish', etc.,
                    # we may not have completion data yet - mark as pending
                    filtered_substages = {}
                    for substage_key in valid_substages:
                        # Try to find matching substage in all_substages_data
                        # For new channel-specific substages, create pending entries
                        if stage_name in all_substages_data and substage_key in all_substages_data[stage_name]:
                            filtered_substages[substage_key] = all_substages_data[stage_name][substage_key]
                        else:
                            # New channel-specific substage - mark as pending
                            filtered_substages[substage_key] = {
                                "status": "pending",
                                "completed_at": None,
                                "progress": 0
                            }
                    
                    if filtered_substages:
                        stage_status = "complete" if all(s.get("status") == "complete" for s in filtered_substages.values()) else ("in_progress" if any(s.get("status") == "in_progress" for s in filtered_substages.values()) else "pending")
                        stage_progress = int(sum(s.get("progress", 0) for s in filtered_substages.values()) / len(filtered_substages)) if filtered_substages else 0
                        filtered_stages[stage_name] = {
                            "status": stage_status,
                            "progress": stage_progress,
                            "substages": filtered_substages
                        }
            
            # Build response
            response_data = {
                "success": True,
                "data": {
                    "post_id": post_id,
                    "post_type": post_type,
                    "output_channel": output_channel,
                    "title": post['title'],
                    "status": post['status'],
                    "overall_progress": overall_progress,
                    "stages": filtered_stages
                }
            }
            
            return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/post-types/<post_type>/substages', methods=['GET'])
def get_substages_for_post_type_api(post_type):
    """Get substages configuration for a post type, optionally filtered by output channel"""
    try:
        from utils.substage_config import get_substages_with_metadata
        
        # Normalize post_type
        if post_type not in ['themed', 'profile', 'generated', 'recipe', 'weekly_word', 'weekly_phrase', 'weekly_insult']:
            post_type = 'themed'
        
        # Get output channel from query parameter (defaults to 'blog')
        output_channel = request.args.get('output', 'blog').lower()
        valid_channels = ['blog', 'facebook', 'instagram', 'twitter', 'newsletter']
        if output_channel not in valid_channels:
            output_channel = 'blog'
        
        # Get output channel configuration
        # Get content format if available
        content_format = None
        try:
            from utils.channel_assignment import get_content_format
            content_format = get_content_format(post_type, output_channel)
        except Exception:
            pass
        
        output_config = get_stages_for_output(post_type, output_channel, content_format)
        
        if output_config.get('use_post_type_config'):
            # Use post_type_substages (blog output)
            stage = request.args.get('stage')
            substages = get_substages_with_metadata(post_type, stage)
        else:
            # Use channel-specific stages
            channel_stages = output_config.get('stages', [])
            channel_substages = output_config.get('substages', {})
            
            stage = request.args.get('stage')
            if stage:
                # Return substages for specific stage
                substage_keys = channel_substages.get(stage, [])
                substages = []
                for key in substage_keys:
                    # Create basic metadata for channel-specific substages
                    substages.append({
                        'key': key,
                        'label': key.replace('_', ' ').title(),
                        'route_function': None,
                        'order': substage_keys.index(key) + 1
                    })
            else:
                # Return all stages with substages
                substages = {}
                for stage_name in channel_stages:
                    substage_keys = channel_substages.get(stage_name, [])
                    substages[stage_name] = []
                    for key in substage_keys:
                        substages[stage_name].append({
                            'key': key,
                            'label': key.replace('_', ' ').title(),
                            'route_function': None,
                            'order': substage_keys.index(key) + 1
                        })
        
        return jsonify({
            "success": True,
            "post_type": post_type,
            "output_channel": output_channel,
            "stage": stage,
            "substages": substages
        })
    except Exception as e:
        logger.error(f"Error getting substages for post type: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/pipeline/<int:post_id>', methods=['GET'])
def get_pipeline_for_post(post_id):
    """Get full pipeline definition for a post, optionally filtered by output channel"""
    try:
        # Get output channel from query parameter (defaults to 'blog')
        output_channel = request.args.get('output', 'blog').lower()
        valid_channels = ['blog', 'facebook', 'instagram', 'twitter', 'newsletter']
        if output_channel not in valid_channels:
            output_channel = 'blog'
        
        with db_manager.get_cursor() as cursor:
            # Get post to determine post_type
            cursor.execute("""
                SELECT p.id, p.recipe_id, p.profile_category_id, p.generated_source_type
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            
            post = cursor.fetchone()
            if not post:
                return jsonify({"success": False, "error": "Post not found"}), 404
            
            # Determine post_type
            if post.get('recipe_id') is not None:
                post_type = 'recipe'
            elif post.get('profile_category_id') is not None:
                post_type = 'profile'
            elif post.get('generated_source_type') is not None:
                post_type = 'generated'
            else:
                post_type = 'themed'
        
        # Get output channel configuration
        # Get content format if available
        content_format = None
        try:
            from utils.channel_assignment import get_content_format
            content_format = get_content_format(post_type, output_channel)
        except Exception:
            pass
        
        output_config = get_stages_for_output(post_type, output_channel, content_format)
        
        # Build pipeline definition
        if output_config.get('use_post_type_config'):
            # Use post_type_substages
            from utils.substage_config import get_substages_with_metadata
            stages_data = get_substages_with_metadata(post_type)
            
            pipeline_stages = []
            for stage_name, substages_list in stages_data.items():
                pipeline_stages.append({
                    'stage': stage_name,
                    'substages': substages_list
                })
        else:
            # Use channel-specific stages
            channel_stages = output_config.get('stages', [])
            channel_substages = output_config.get('substages', {})
            
            pipeline_stages = []
            for stage_name in channel_stages:
                substage_keys = channel_substages.get(stage_name, [])
                substages_list = []
                for key in substage_keys:
                    substages_list.append({
                        'key': key,
                        'label': key.replace('_', ' ').title(),
                        'route_function': None,
                        'order': substage_keys.index(key) + 1
                    })
                pipeline_stages.append({
                    'stage': stage_name,
                    'substages': substages_list
                })
        
        return jsonify({
            "success": True,
            "data": {
                "post_id": post_id,
                "post_type": post_type,
                "output_channel": output_channel,
                "stages": pipeline_stages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline for post: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/posts-in-development', methods=['GET'])
def get_posts_in_development():
    """Get list of posts in development"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.created_at, p.updated_at,
                       pd.expanded_idea, pd.idea_seed, pd.sections,
                       pd.topic_allocation, pd.section_structure, pd.idea_scope
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                WHERE p.status IN ('draft', 'in_process')
                ORDER BY p.updated_at DESC
            """)
            
            posts = cursor.fetchall()
            
            # Calculate progress for each post
            posts_with_progress = []
            for post in posts:
                # Count completed sections
                cursor.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 ELSE 0 END) as drafted
                    FROM post_section
                    WHERE post_id = %s
                """, (post['id'],))
                
                section_stats = cursor.fetchone()
                
                # Calculate progress
                planning_complete = bool(post['topic_allocation'] and post['section_structure'])
                authoring_progress = 0
                if section_stats and section_stats['total'] > 0:
                    authoring_progress = int((section_stats['drafted'] / section_stats['total']) * 100)
                
                overall_progress = 0
                if planning_complete:
                    overall_progress += 40
                overall_progress += int(authoring_progress * 0.6)
                
                posts_with_progress.append({
                    "id": post['id'],
                    "title": post['title'],
                    "status": post['status'],
                    "created_at": post['created_at'].isoformat() if post['created_at'] else None,
                    "updated_at": post['updated_at'].isoformat() if post['updated_at'] else None,
                    "expanded_idea": post['expanded_idea'],
                    "idea_seed": post['idea_seed'],
                    "progress": overall_progress,
                    "planning_complete": planning_complete,
                    "authoring_progress": authoring_progress
                })
            
            return jsonify({
                "success": True,
                "data": posts_with_progress
            })
            
    except Exception as e:
        logger.error(f"Error getting posts in development: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def _calendar_week_url_from_date(from_date):
    """Build /planning/calendar?year=Y&week=W&tab=week-view from from_date (date or date string)."""
    if hasattr(from_date, "isocalendar"):
        year, week, _ = from_date.isocalendar()
    else:
        d = datetime.strptime(str(from_date)[:10], "%Y-%m-%d").date()
        year, week, _ = d.isocalendar()
    return f"/planning/calendar?year={year}&week={week}&tab=week-view"


@bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts. Phase 2.5: Hybrid run alerts from hybrid_run_summaries."""
    try:
        alerts = []
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, run_timestamp, platform, from_date, weeks_ahead,
                       coverage_status, run_outcome, confidence_statement, summary_text,
                       any_human_action_required, human_action_counts, coverage_summary,
                       acknowledged_at
                FROM hybrid_run_summaries
                WHERE platform = %s
                ORDER BY run_timestamp DESC
                LIMIT 1
            """, ("instagram",))
            row = cursor.fetchone()

        if not row:
            alerts.append({
                "id": 0,
                "alert_type": "hybrid_never",
                "severity": "warning",
                "title": "Instagram imagery not yet run",
                "message": "Instagram imagery has never been generated.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_read": False,
                "action_url": "/planning/calendar?tab=week-view",
                "action_text": "View calendar",
            })
            return jsonify({"success": True, "data": alerts})

        run_ts = row["run_timestamp"]
        if run_ts.tzinfo is None:
            run_ts = run_ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(hours=24)
        from_date = row["from_date"]
        action_url = _calendar_week_url_from_date(from_date)
        summary_id = row["id"]
        # Phase 2.6: only show alerts for this run if not yet acknowledged (e.g. user has not opened Launchpad)
        acknowledged = row.get("acknowledged_at") is not None

        if not acknowledged and run_ts < stale_threshold:
            alerts.append({
                "id": summary_id * 100 + 1,
                "alert_type": "hybrid_stale",
                "severity": "warning",
                "title": "Instagram imagery automation stale",
                "message": "Instagram imagery automation hasn't run recently.",
                "created_at": run_ts.isoformat(),
                "is_read": False,
                "action_url": action_url,
                "action_text": "View calendar",
            })
        if not acknowledged and row["run_outcome"] == "blocked":
            alerts.append({
                "id": summary_id * 100 + 2,
                "alert_type": "hybrid_blocked",
                "severity": "error",
                "title": "Instagram imagery run blocked",
                "message": row["confidence_statement"] or "Run reported blocked.",
                "created_at": run_ts.isoformat(),
                "is_read": False,
                "action_url": action_url,
                "action_text": "View calendar",
            })
        if not acknowledged and row["coverage_status"] != "complete":
            alerts.append({
                "id": summary_id * 100 + 3,
                "alert_type": "hybrid_incomplete",
                "severity": "warning",
                "title": "Instagram imagery incomplete",
                "message": row["confidence_statement"] or row["summary_text"] or "Coverage not complete.",
                "created_at": run_ts.isoformat(),
                "is_read": False,
                "action_url": action_url,
                "action_text": "View calendar",
            })
        if not acknowledged and row["any_human_action_required"]:
            alerts.append({
                "id": summary_id * 100 + 4,
                "alert_type": "hybrid_human_action",
                "severity": "warning",
                "title": "Instagram imagery needs attention",
                "message": row["confidence_statement"] or "Some slots need human action.",
                "created_at": run_ts.isoformat(),
                "is_read": False,
                "action_url": action_url,
                "action_text": "View calendar",
            })

        return jsonify({"success": True, "data": alerts})

    except Exception as e:
        logger.exception("Error getting alerts")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/alert/dismiss/<int:alert_id>', methods=['POST'])
def dismiss_alert():
    """Dismiss an alert"""
    try:
        # For now, just return success - in a real implementation,
        # you might want to store dismissed alerts in a database
        return jsonify({
            "success": True,
            "message": "Alert dismissed"
        })
        
    except Exception as e:
        logger.error(f"Error dismissing alert: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/analytics/<int:post_id>', methods=['GET'])
def get_post_analytics(post_id):
    """Get analytics for a published post"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post basic info
            cursor.execute("""
                SELECT p.id, p.title, p.status, p.published_at, p.created_at
                FROM post p
                WHERE p.id = %s AND p.status = 'published'
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return jsonify({"success": False, "error": "Published post not found"}), 404
            
            # Mock analytics data - in a real implementation, you'd query actual analytics
            analytics_data = {
                "post_id": post_id,
                "title": post['title'],
                "published_at": post['published_at'].isoformat() if post['published_at'] else None,
                "views": 0,  # Would come from analytics service
                "clicks": 0,  # Would come from analytics service
                "engagement": 0,  # Would come from analytics service
                "social_shares": 0,  # Would come from analytics service
                "conversion_rate": 0.0  # Would come from analytics service
            }
            
            return jsonify({
                "success": True,
                "data": analytics_data
            })
            
    except Exception as e:
        logger.error(f"Error getting post analytics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
