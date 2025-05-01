"""Routes for LLM-powered content generation and enhancement."""

from flask import jsonify, request, current_app, render_template
import logging
from app.models import Post, PostSection, LLMPrompt, LLMInteraction, LLMConfig, db, LLMAction, LLMActionHistory
from .chains import (
    create_idea_generation_chain,
    create_content_expansion_chain,
    create_seo_optimization_chain,
    generate_social_media_content,
)
from datetime import datetime
from app.llm import bp
from app.llm.services import LLMService

logger = logging.getLogger(__name__)


@bp.route("/")
def index():
    """LLM management interface."""
    config = LLMConfig.query.first()
    prompts = {template.name: template.prompt_text for template in LLMPrompt.query.all()}
    return render_template("llm/index.html", config=config, prompts=prompts)


@bp.route("/api/v1/llm/generate-idea", methods=["POST"])
def generate_idea():
    """Generate a blog post idea."""
    data = request.get_json()
    topic = data.get("topic")
    style = data.get("style", "informative")
    audience = data.get("audience", "Scottish heritage enthusiasts")

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

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
            parameters={"temperature": chain.llm.temperature},
            duration=duration,
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/v1/llm/expand-section/<int:section_id>", methods=["POST"])
def expand_section(section_id):
    """Expand a section's content."""
    section = PostSection.query.get_or_404(section_id)
    data = request.get_json()
    tone = data.get("tone", "professional")
    platforms = data.get("platforms", ["blog"])

    try:
        chain = create_content_expansion_chain()
        start_time = datetime.utcnow()
        result = chain.run(
            title=section.title,
            summary=section.subtitle or section.title,
            tone=tone,
            platforms=platforms,
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
            parameters={"temperature": chain.llm.temperature},
            duration=duration,
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/v1/llm/optimize-seo/<int:post_id>", methods=["POST"])
def optimize_seo(post_id):
    """Get SEO optimization suggestions for a post."""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    keywords = data.get("keywords", [])

    try:
        chain = create_seo_optimization_chain()
        start_time = datetime.utcnow()

        # Combine all section content
        content = "\n\n".join(
            [f"# {section.title}\n{section.content}" for section in post.sections]
        )

        result = chain.run(content=content, keywords=keywords)
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Record the interaction
        interaction = LLMInteraction(
            prompt_id=None,
            post_id=post.id,
            input_text=f"Post: {post.title}, Keywords: {keywords}",
            output_text=str(result),
            model_used=chain.llm.model_name,
            parameters={"temperature": chain.llm.temperature},
            duration=duration,
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify({"suggestions": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/v1/llm/generate-social/<int:section_id>", methods=["POST"])
def generate_social(section_id):
    """Generate social media content for a section."""
    section = PostSection.query.get_or_404(section_id)
    data = request.get_json()
    platforms = data.get("platforms", ["tiktok", "instagram"])

    try:
        start_time = datetime.utcnow()
        result = generate_social_media_content(section, platforms)
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Update the section's social media snippets
        current_snippets = section.social_media_snippets or {}
        section.social_media_snippets = {**current_snippets, **result}

        # Record the interaction
        interaction = LLMInteraction(
            prompt_id=None,
            post_id=section.post_id,
            input_text=f"Section: {section.title}, Platforms: {platforms}",
            output_text=str(result),
            model_used="gpt-4",  # This should match your OpenAI model configuration
            parameters={"platforms": platforms},
            duration=duration,
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route('/api/v1/llm/log', methods=['POST'])
def log_message():
    """Log a message to the Flask logger"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    logger.info(f"\n=== LLM PROMPT DEBUG ===\n{data['message']}\n=====================")
    return jsonify({'status': 'success'}), 200


@bp.route('/actions')
def actions():
    """Render the LLM Actions management page."""
    actions = LLMAction.query.all()
    prompts = LLMPrompt.query.all()
    config = LLMConfig.query.first()
    if not config:
        config = LLMConfig(
            provider_type="ollama",
            model_name="mistral",
            api_base="http://localhost:11434"
        )
        db.session.add(config)
        db.session.commit()
    
    from app.blog.fields import WORKFLOW_FIELDS
    return render_template(
        'llm/actions.html',
        actions=actions,
        prompts=prompts,
        config=config,
        workflow_fields=WORKFLOW_FIELDS
    )

@bp.route('/api/v1/llm/actions', methods=['GET', 'POST'])
def handle_actions():
    """Handle LLM actions list and creation."""
    if request.method == 'GET':
        actions = LLMAction.query.all()
        return jsonify([action.to_dict() for action in actions])
    
    data = request.get_json()
    try:
        # Get the prompt template
        prompt_template = LLMPrompt.query.get_or_404(data['prompt_template_id'])
        
        action = LLMAction(
            field_name=data['field_name'],
            source_field=data['source_field'],
            prompt_template=prompt_template.prompt_text,
            llm_model=data['llm_model'],
            temperature=data['temperature'],
            max_tokens=data['max_tokens']
        )
        db.session.add(action)
        db.session.commit()
        return jsonify({'status': 'success', 'action': action.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error creating action: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 400

@bp.route('/api/v1/llm/actions/<int:action_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_action(action_id):
    """Handle individual LLM action operations."""
    action = LLMAction.query.get_or_404(action_id)
    
    if request.method == 'GET':
        return jsonify(action.to_dict())
    
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            # Get the prompt template if it's being updated
            if 'prompt_template_id' in data:
                prompt_template = LLMPrompt.query.get_or_404(data['prompt_template_id'])
                action.prompt_template = prompt_template.prompt_text
            
            if 'field_name' in data:
                action.field_name = data['field_name']
            if 'source_field' in data:
                action.source_field = data['source_field']
            if 'llm_model' in data:
                action.llm_model = data['llm_model']
            if 'temperature' in data:
                action.temperature = data['temperature']
            if 'max_tokens' in data:
                action.max_tokens = data['max_tokens']
            
            db.session.commit()
            return jsonify({'status': 'success', 'action': action.to_dict()})
        except Exception as e:
            current_app.logger.error(f"Error updating action: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(action)
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            current_app.logger.error(f"Error deleting action: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 400

@bp.route('/api/v1/llm/actions/<int:action_id>/history')
def action_history(action_id):
    """Get the history for a specific LLM action."""
    action = LLMAction.query.get_or_404(action_id)
    history = LLMActionHistory.query.filter_by(action_id=action_id).order_by(LLMActionHistory.timestamp.desc()).all()
    return jsonify({
        'action': action.to_dict(),
        'history': [h.to_dict() for h in history]
    })

@bp.route('/api/v1/llm/models/ollama')
def get_ollama_models():
    """Get available Ollama models."""
    # TODO: Implement actual Ollama model listing
    # For now, return a static list of models
    return jsonify({
        'models': ['llama2', 'codellama', 'mistral', 'mixtral'],
        'loaded': ['llama2', 'mistral']  # Models currently loaded in memory
    })

@bp.route('/api/v1/llm/test', methods=['POST'])
def test_llm():
    """Test an LLM prompt with specified model and parameters."""
    data = request.get_json()
    if not data or 'prompt' not in data or 'model_name' not in data or 'input' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    prompt = data['prompt'].replace('{{input}}', data['input'])
    model_name = data['model_name']
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 1000)

    try:
        # Record the test interaction
        start_time = datetime.utcnow()
        
        # Initialize LLM service
        llm_service = LLMService()
        result = llm_service.generate(prompt, model_name)
        
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log the test interaction
        interaction = LLMInteraction(
            prompt_id=None,  # No prompt ID for tests
            input_text=prompt,
            output_text=result,
            parameters_used={
                'model': model_name,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'input': data['input']
            },
            interaction_metadata={
                'duration': duration,
                'test': True
            }
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify({
            'result': result,
            'model': model_name,
            'duration': duration
        })
    except Exception as e:
        logger.error(f"Error in test_llm: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/v1/llm/templates')
def get_templates():
    """Get available prompt templates."""
    templates = LLMPrompt.query.all()
    return jsonify([{
        'id': template.id,
        'name': template.name,
        'description': template.description,
        'prompt_text': template.prompt_text
    } for template in templates])

@bp.route('/api/v1/llm/config', methods=['GET', 'POST'])
def handle_llm_config():
    """Get or update LLM configuration."""
    if request.method == 'GET':
        config = LLMConfig.query.first()
        if not config:
            config = LLMConfig(
                provider_type="ollama",
                model_name="mistral",
                api_base="http://localhost:11434"
            )
            db.session.add(config)
            db.session.commit()
        
        return jsonify({
            'provider_type': config.provider_type,
            'model_name': config.model_name,
            'api_base': config.api_base
        })
    
    # Handle POST request
    data = request.get_json()
    try:
        config = LLMConfig.query.first()
        if not config:
            config = LLMConfig()
            db.session.add(config)
        
        if 'provider_type' in data:
            config.provider_type = data['provider_type']
        if 'model_name' in data:
            config.model_name = data['model_name']
        if 'api_base' in data:
            config.api_base = data['api_base']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error updating LLM config: {str(e)}")
        return jsonify({'error': str(e)}), 400

@bp.route('/api/v1/llm/prompts')
def get_prompts():
    """Get available prompt templates."""
    prompts = LLMPrompt.query.all()
    return jsonify([{
        'id': prompt.id,
        'name': prompt.name,
        'description': prompt.description,
        'prompt_text': prompt.prompt_text
    } for prompt in prompts])
