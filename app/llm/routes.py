"""Routes for LLM-powered content generation and enhancement."""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
import logging
from app.models import Post, PostSection, LLMPrompt, LLMInteraction, db
from .chains import (
    create_idea_generation_chain,
    create_content_expansion_chain,
    create_seo_optimization_chain,
    generate_social_media_content
)
from datetime import datetime

bp = Blueprint('llm', __name__)
logger = logging.getLogger(__name__)

@bp.route('/api/llm/generate-idea', methods=['POST'])
@login_required
def generate_idea():
    """Generate a blog post idea."""
    data = request.get_json()
    topic = data.get('topic')
    style = data.get('style', 'informative')
    audience = data.get('audience', 'Scottish heritage enthusiasts')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
        
    try:
        chain = create_idea_generation_chain()
        start_time = datetime.utcnow()
        result = chain.run(topic=topic, style=style, audience=audience)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Record the interaction
        interaction = LLMInteraction(
            prompt_id=None,  # Could link to a stored prompt if needed
            input_text=f"Topic: {topic}, Style: {style}, Audience: {audience}",
            output_text=str(result),
            model_used=chain.llm.model_name,
            parameters={'temperature': chain.llm.temperature},
            duration=duration
        )
        db.session.add(interaction)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/expand-section/<int:section_id>', methods=['POST'])
@login_required
def expand_section(section_id):
    """Expand a section's content."""
    section = PostSection.query.get_or_404(section_id)
    data = request.get_json()
    tone = data.get('tone', 'professional')
    platforms = data.get('platforms', ['blog'])
    
    try:
        chain = create_content_expansion_chain()
        start_time = datetime.utcnow()
        result = chain.run(
            title=section.title,
            summary=section.subtitle or section.title,
            tone=tone,
            platforms=platforms
        )
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Update the section with expanded content
        section.content = result.content
        section.keywords = result.keywords
        section.social_media_snippets = result.social_media_snippets
        
        # Record the interaction
        interaction = LLMInteraction(
            prompt_id=None,
            post_id=section.post_id,
            input_text=f"Section: {section.title}, Tone: {tone}",
            output_text=str(result),
            model_used=chain.llm.model_name,
            parameters={'temperature': chain.llm.temperature},
            duration=duration
        )
        db.session.add(interaction)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/optimize-seo/<int:post_id>', methods=['POST'])
@login_required
def optimize_seo(post_id):
    """Get SEO optimization suggestions for a post."""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    keywords = data.get('keywords', [])
    
    try:
        chain = create_seo_optimization_chain()
        start_time = datetime.utcnow()
        
        # Combine all section content
        content = "\n\n".join([
            f"# {section.title}\n{section.content}"
            for section in post.sections
        ])
        
        result = chain.run(content=content, keywords=keywords)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Record the interaction
        interaction = LLMInteraction(
            prompt_id=None,
            post_id=post.id,
            input_text=f"Post: {post.title}, Keywords: {keywords}",
            output_text=str(result),
            model_used=chain.llm.model_name,
            parameters={'temperature': chain.llm.temperature},
            duration=duration
        )
        db.session.add(interaction)
        db.session.commit()
        
        return jsonify({'suggestions': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/llm/generate-social/<int:section_id>', methods=['POST'])
@login_required
def generate_social(section_id):
    """Generate social media content for a section."""
    section = PostSection.query.get_or_404(section_id)
    data = request.get_json()
    platforms = data.get('platforms', ['tiktok', 'instagram'])
    
    try:
        start_time = datetime.utcnow()
        result = generate_social_media_content(section, platforms)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Update the section's social media snippets
        current_snippets = section.social_media_snippets or {}
        section.social_media_snippets = {
            **current_snippets,
            **result
        }
        
        # Record the interaction
        interaction = LLMInteraction(
            prompt_id=None,
            post_id=section.post_id,
            input_text=f"Section: {section.title}, Platforms: {platforms}",
            output_text=str(result),
            model_used="gpt-4",  # This should match your OpenAI model configuration
            parameters={'platforms': platforms},
            duration=duration
        )
        db.session.add(interaction)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 