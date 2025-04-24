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

    def generate(self, prompt):
        """Generate text using configured LLM"""
        if self.config.provider_type == "ollama":
            return self._generate_ollama(prompt)
        elif self.config.provider_type == "openai":
            return self._generate_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider type: {self.config.provider_type}")

    def _generate_ollama(self, prompt):
        """Generate text using Ollama"""
        url = f"{self.config.api_base}/api/generate"

        data = {"model": self.config.model_name, "prompt": prompt, "stream": False}

        response = httpx.post(url, json=data)
        response.raise_for_status()

        return response.json()["response"]

    def _generate_openai(self, prompt):
        """Generate text using OpenAI"""
        if not self.config.auth_token:
            raise ValueError("Authentication token not configured")

        url = f"{self.config.api_base}/v1/chat/completions"

        headers = self._get_headers()

        data = {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        response = httpx.post(url, headers=headers, json=data)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _get_headers(self):
        """Get headers for API requests"""
        if not self.config.auth_token:
            raise ValueError("Authentication token not configured")

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.auth_token}",
        }
