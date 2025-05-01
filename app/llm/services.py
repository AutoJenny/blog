"""Service for interacting with LLM providers."""

import httpx
import logging
from flask import current_app
from app.models import LLMConfig, LLMInteraction
from app import db
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM providers."""

    def __init__(self):
        """Initialize the LLM service."""
        self.config = LLMConfig.query.first()
        if not self.config:
            self.config = LLMConfig(
                provider_type="ollama",
                model_name="mistral",
                api_base="http://localhost:11434",
            )

    def generate(self, prompt, model_name=None, temperature=0.7, max_tokens=1000):
        """Generate text using configured LLM, optionally specifying a model name."""
        if not model_name:
            model_name = self.config.model_name

        if self.config.provider_type == "ollama":
            return self._generate_ollama(prompt, model_name, temperature, max_tokens)
        elif self.config.provider_type == "openai":
            return self._generate_openai(prompt, model_name, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider type: {self.config.provider_type}")

    def _generate_ollama(self, prompt, model_name, temperature=0.7, max_tokens=1000):
        """Generate text using Ollama."""
        try:
            response = httpx.post(
                f"{self.config.api_base}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Error generating with Ollama: {str(e)}")
            raise

    def _generate_openai(self, prompt, model_name, temperature=0.7, max_tokens=1000):
        """Generate text using OpenAI."""
        try:
            import openai
            client = openai.OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {str(e)}")
            raise

    def execute_action(self, action, post_id, input_text):
        """Execute an LLM action on a post field."""
        try:
            # Format the prompt template with the input
            prompt = action.prompt_template.replace("{{input}}", input_text)
            
            # Create history record
            history = LLMActionHistory(
                action_id=action.id,
                post_id=post_id,
                input_text=input_text,
                status="pending"
            )
            db.session.add(history)
            db.session.commit()
            
            try:
                # Generate the output
                output = self.generate(
                    prompt,
                    model_name=action.llm_model,
                    temperature=action.temperature,
                    max_tokens=action.max_tokens
                )
                
                # Update history record
                history.output_text = output
                history.status = "success"
                db.session.commit()
                
                return output
            except Exception as e:
                # Update history record with error
                history.status = "error"
                history.error_message = str(e)
                db.session.commit()
                raise
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            raise 