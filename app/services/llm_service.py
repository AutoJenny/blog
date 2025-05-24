from flask import current_app
import openai
import time
from typing import Optional, Dict, Any
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback
import os


class ServiceAuth:
    """Handle service authentication"""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class LLMService:
    def __init__(self):
        """Initialize the LLM service"""
        auth = current_app.config.get("OPENAI_AUTH_TOKEN")
        if not auth:
            raise ValueError("Authentication token not configured")

        self.client = openai.OpenAI(auth=ServiceAuth(auth))
        self.chat_model = ChatOpenAI(
            model_name=current_app.config["LLM_MODEL"], temperature=0.7
        )

    def process_post_content(
        self, post_id: int, prompt_name: str, **kwargs
    ) -> Dict[str, Any]:
        """Process a blog post with a specific LLM prompt."""
        try:
            formatted_prompt = f"You are a helpful AI assistant for blog content processing. Post ID: {post_id}, Prompt Name: {prompt_name}, **kwargs: {kwargs}"

            start_time = time.time()
            with get_openai_callback() as cb:
                response = self.chat_model.predict_messages(
                    [
                        SystemMessage(
                            content="You are a helpful AI assistant for blog content processing."
                        ),
                        HumanMessage(content=formatted_prompt),
                    ]
                )
            duration = time.time() - start_time

            # Record the interaction
            interaction = {
                "prompt_id": post_id,
                "post_id": post_id,
                "input_text": formatted_prompt,
                "output_text": response.content,
                "model_used": current_app.config["LLM_MODEL"],
                "parameters": {
                    "temperature": current_app.config["LLM_TEMPERATURE"],
                    "max_tokens": current_app.config["LLM_MAX_TOKENS"],
                    **kwargs,
                },
                "tokens_used": cb.total_tokens,
                "duration": duration,
            }
            return interaction
        except Exception as e:
            current_app.logger.error(f"Error processing post content: {str(e)}")
            raise

    def generate_post_summary(
        self, post_id: int, max_length: Optional[int] = 200
    ) -> str:
        """Generate a summary for a blog post."""
        return self.process_post_content(
            post_id=post_id, prompt_name="generate_summary", max_length=max_length
        )["output_text"]

    def suggest_tags(self, post_id: int, max_tags: Optional[int] = 5) -> list:
        """Suggest tags for a blog post."""
        response = self.process_post_content(
            post_id=post_id, prompt_name="suggest_tags", max_tags=max_tags
        )
        return response["output_text"].strip().split(",")

    def enhance_seo(self, post_id: int) -> Dict[str, Any]:
        """Enhance SEO for a blog post."""
        return self.process_post_content(post_id=post_id, prompt_name="enhance_seo")

    def improve_readability(self, post_id: int) -> Dict[str, str]:
        """Improve the readability of a blog post."""
        return self.process_post_content(
            post_id=post_id, prompt_name="improve_readability"
        )

    def generate_social_media_content(self, post_id: int, platform: str) -> str:
        """Generate social media content for a blog post."""
        return self.process_post_content(
            post_id=post_id, prompt_name="social_media_content", platform=platform
        )["output_text"]
