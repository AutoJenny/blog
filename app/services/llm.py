import httpx
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
        url = f"{self.config.api_base}/api/generate"
        model = model_name if model_name else self.config.model_name
        data = {"model": model, "prompt": prompt, "stream": False}
        try:
            response = httpx.post(url, json=data, timeout=60.0)
            response.raise_for_status()
            return {"response": response.json()["response"], "model_used": model}
        except httpx.TimeoutException:
            raise RuntimeError("LLM backend timed out. Please try again later.")
        except httpx.RequestError as e:
            raise RuntimeError(f"LLM backend connection error: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM backend error: {e}")

    def _generate_openai(self, prompt, model_name=None):
        """Generate text using OpenAI"""
        if not self.config.auth_token:
            raise ValueError("Authentication token not configured")
        url = f"{self.config.api_base}/v1/chat/completions"
        headers = self._get_headers()
        model = model_name if model_name else self.config.model_name
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        try:
            response = httpx.post(url, headers=headers, json=data, timeout=60.0)
            response.raise_for_status()
            return {"response": response.json()["choices"][0]["message"]["content"], "model_used": model}
        except httpx.TimeoutException:
            raise RuntimeError("LLM backend timed out. Please try again later.")
        except httpx.RequestError as e:
            raise RuntimeError(f"LLM backend connection error: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM backend error: {e}")

    def _get_headers(self):
        """Get headers for API requests"""
        if not self.config.auth_token:
            raise ValueError("Authentication token not configured")

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.auth_token}",
        }
