# DEPRECATED: Use app.llm.services instead.

# This file is deprecated and should not be used. All LLM service logic has been moved to app/llm/services.py.

from typing import Dict, Any, Optional
from flask import current_app

def execute_request(request_data: Dict[str, Any], provider: str = 'ollama', model: str = 'llama3.1:70b') -> Optional[str]:
    """Execute an LLM request."""
    current_app.logger.info(f"[LLM Request] Provider: {provider}, Model: {model}")
    current_app.logger.info(f"[LLM Request] API Endpoint: {OLLAMA_API_ENDPOINT}")
    current_app.logger.info(f"[LLM Request] Prompt: {request_data.get('prompt')}")
    
    # For testing, return a fixed response
    return "This is a test response for format validation"
