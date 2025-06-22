import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.config = None
        self.api_url = None

    def generate(self, prompt: str, model_name: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate text using the configured LLM."""
        if not self.config:
            raise ValueError("LLM configuration not set")

        if self.config == "ollama":
            return self._generate_ollama(prompt, model_name, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config}")

    def _generate_ollama(self, prompt: str, model_name: str, temperature: float, max_tokens: int) -> str:
        """Generate text using Ollama."""
        api_url = self.api_url or "http://localhost:11434"
        try:
            response = requests.post(f"{api_url}/api/generate", json={
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            raise

def execute_llm_request(prompt: str, model_name: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
    """Execute an LLM request using the default service."""
    service = LLMService()
    service.config = "ollama"  # Default to Ollama
    return service.generate(prompt, model_name, temperature, max_tokens)

def log_llm_outgoing(prompt: str, model_name: str, temperature: float, max_tokens: int) -> None:
    """Log outgoing LLM request details."""
    logger.info(f"LLM Request: model={model_name}, temp={temperature}, max_tokens={max_tokens}")
    logger.debug(f"Prompt: {prompt}")

def modular_prompt_to_canonical(prompt_parts: Dict[str, Any]) -> str:
    """Convert a modular prompt structure to a canonical string format."""
    # For now, just concatenate system and task prompts
    system_prompt = prompt_parts.get("system_prompt", "")
    task_prompt = prompt_parts.get("task_prompt", "")
    return f"{system_prompt}\n\n{task_prompt}" 