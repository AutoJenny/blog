from flask import current_app
from app.models import LLMPrompt, LLMInteraction, Post
from app import db
import openai
import time
from typing import Optional, Dict, Any
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback

class LLMService:
    def __init__(self):
        if not current_app.config.get('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key not configured")
            
        self.client = openai.OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
        self.chat_model = ChatOpenAI(
            model_name=current_app.config['LLM_MODEL'],
            temperature=current_app.config['LLM_TEMPERATURE'],
            max_tokens=current_app.config['LLM_MAX_TOKENS']
        )
    
    def process_post_content(self, post_id: int, prompt_name: str, **kwargs) -> Dict[str, Any]:
        """Process a blog post with a specific LLM prompt."""
        try:
            post = Post.query.get_or_404(post_id)
            prompt = LLMPrompt.query.filter_by(name=prompt_name).first_or_404()
            
            formatted_prompt = prompt.get_formatted_prompt(
                post_title=post.title,
                post_content=post.content,
                **kwargs
            )
            
            start_time = time.time()
            with get_openai_callback() as cb:
                response = self.chat_model.predict_messages([
                    SystemMessage(content="You are a helpful AI assistant for blog content processing."),
                    HumanMessage(content=formatted_prompt)
                ])
            duration = time.time() - start_time
            
            # Record the interaction
            interaction = LLMInteraction(
                prompt_id=prompt.id,
                post_id=post.id,
                input_text=formatted_prompt,
                output_text=response.content,
                model_used=current_app.config['LLM_MODEL'],
                parameters={
                    'temperature': current_app.config['LLM_TEMPERATURE'],
                    'max_tokens': current_app.config['LLM_MAX_TOKENS'],
                    **kwargs
                },
                tokens_used=cb.total_tokens,
                duration=duration
            )
            db.session.add(interaction)
            db.session.commit()
            
            return interaction.to_dict()
        except Exception as e:
            current_app.logger.error(f"Error processing post content: {str(e)}")
            db.session.rollback()
            raise
    
    def generate_post_summary(self, post_id: int, max_length: Optional[int] = 200) -> str:
        """Generate a summary for a blog post."""
        return self.process_post_content(
            post_id=post_id,
            prompt_name='generate_summary',
            max_length=max_length
        )['output_text']
    
    def suggest_tags(self, post_id: int, max_tags: Optional[int] = 5) -> list:
        """Suggest tags for a blog post."""
        response = self.process_post_content(
            post_id=post_id,
            prompt_name='suggest_tags',
            max_tags=max_tags
        )
        return response['output_text'].strip().split(',')
    
    def enhance_seo(self, post_id: int) -> Dict[str, Any]:
        """Enhance SEO for a blog post."""
        return self.process_post_content(
            post_id=post_id,
            prompt_name='enhance_seo'
        )
    
    def improve_readability(self, post_id: int) -> Dict[str, str]:
        """Improve the readability of a blog post."""
        return self.process_post_content(
            post_id=post_id,
            prompt_name='improve_readability'
        )
    
    def generate_social_media_content(self, post_id: int, platform: str) -> str:
        """Generate social media content for a blog post."""
        return self.process_post_content(
            post_id=post_id,
            prompt_name='social_media_content',
            platform=platform
        )['output_text'] 