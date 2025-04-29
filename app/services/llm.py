import httpx
import logging
from flask import current_app
from app.models import LLMConfig


class LLMService:
    """Service for interacting with LLM providers"""

    def __init__(self):
        self.config = LLMConfig.query.first()
        if not self.config:
            self.config = LLMConfig(
                provider_type="ollama",
                model_name="mistral",
                api_base="http://localhost:11434",
            )

    def generate(self, prompt, model_name=None):
        """Generate text using configured LLM, optionally specifying a model name"""
        if self.config.provider_type == "ollama":
            return self._generate_ollama(prompt, model_name)
        elif self.config.provider_type == "openai":
            return self._generate_openai(prompt, model_name)
        else:
            raise ValueError(f"Unsupported provider type: {self.config.provider_type}")

    def _generate_ollama(self, prompt, model_name=None):
        """Generate text using Ollama"""
        model = model_name if model_name else self.config.model_name
        base_url = self.config.api_base

        # First check if model is loaded
        try:
            current_app.logger.info(f"Checking if model {model} is loaded...")
            ps_response = httpx.get(f"{base_url}/api/ps", timeout=5.0)
            ps_response.raise_for_status()
            loaded_models = [m["name"] for m in ps_response.json().get("models", [])]
            
            # If model not loaded, try to load it
            if model not in loaded_models:
                current_app.logger.info(f"Model {model} not loaded, attempting to load...")
                try:
                    load_response = httpx.post(
                        f"{base_url}/api/generate",
                        json={"model": model, "prompt": "", "stream": False},
                        timeout=60.0  # Increased timeout for model loading
                    )
                    load_response.raise_for_status()
                    current_app.logger.info(f"Model {model} loaded successfully")
                except httpx.TimeoutException:
                    current_app.logger.warning(f"Timeout while loading model {model}")
                    # Continue anyway - the model might still be loading in the background
                except Exception as e:
                    current_app.logger.error(f"Error loading model {model}: {str(e)}")
                    # Continue anyway - the model might still work

        except httpx.TimeoutException:
            current_app.logger.warning(f"Timeout while checking model {model} status")
            # Continue anyway - the model might still work
        except Exception as e:
            current_app.logger.error(f"Error checking model status: {str(e)}")
            # Continue anyway - the model might still work

        # Now try to generate
        url = f"{base_url}/api/generate"
        data = {"model": model, "prompt": prompt, "stream": False}
        try:
            current_app.logger.info(f"Generating response with model {model}...")
            response = httpx.post(url, json=data, timeout=60.0)
            response.raise_for_status()
            current_app.logger.info(f"Successfully generated response with model {model}")
            return {"response": response.json()["response"], "model_used": model}
        except httpx.TimeoutException:
            current_app.logger.error(f"Timeout during generation with model {model}")
            raise RuntimeError(
                f"LLM request timed out after 60 seconds. Model {model} may still be loading - "
                "please wait a moment and try again. If this persists, try preloading the model "
                "or using a different model."
            )
        except httpx.RequestError as e:
            current_app.logger.error(f"Connection error during generation with model {model}: {str(e)}")
            raise RuntimeError(
                f"Could not connect to LLM backend ({str(e)}). Please check that Ollama "
                "is running and accessible at {base_url}"
            )
        except Exception as e:
            current_app.logger.error(f"Unexpected error during generation with model {model}: {str(e)}")
            raise RuntimeError(f"Unexpected error during LLM generation: {str(e)}")

    def _generate_openai(self, prompt, model_name=None):
        """Generate text using OpenAI"""
        if not self.config.auth_token:
            raise ValueError("OpenAI authentication token not configured")
        url = f"{self.config.api_base}/v1/chat/completions"
        headers = self._get_headers()
        model = model_name if model_name else self.config.model_name
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        try:
            current_app.logger.info(f"Generating response with OpenAI model {model}...")
            response = httpx.post(url, headers=headers, json=data, timeout=60.0)
            response.raise_for_status()
            current_app.logger.info(f"Successfully generated response with OpenAI model {model}")
            return {"response": response.json()["choices"][0]["message"]["content"], "model_used": model}
        except httpx.TimeoutException:
            current_app.logger.error(f"Timeout during generation with OpenAI model {model}")
            raise RuntimeError(
                "OpenAI request timed out after 60 seconds. The service may be experiencing "
                "high load - please try again in a moment."
            )
        except httpx.RequestError as e:
            current_app.logger.error(f"Connection error during generation with OpenAI model {model}: {str(e)}")
            raise RuntimeError(
                f"Could not connect to OpenAI API ({str(e)}). Please check your internet "
                "connection and the API base URL configuration."
            )
        except Exception as e:
            current_app.logger.error(f"Unexpected error during generation with OpenAI model {model}: {str(e)}")
            raise RuntimeError(f"Unexpected error during OpenAI generation: {str(e)}")

    def _get_headers(self):
        """Get headers for API requests"""
        if not self.config.auth_token:
            raise ValueError("Authentication token not configured")

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.auth_token}",
        }
