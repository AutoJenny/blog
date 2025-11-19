"""LLM Service for header blueprint"""
import logging
import os
import requests

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'base_url': 'https://api.openai.com/v1',
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            'ollama': {
                'base_url': 'http://localhost:11434'
            }
        }
    
    def execute_llm_request(self, provider, model, messages, api_key=None):
        """Execute LLM request."""
        try:
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key or self.providers["openai"]["api_key"]}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
            elif provider == 'ollama':
                data = {
                    'model': model,
                    'messages': messages,
                    'stream': False,
                    'options': {
                        'num_predict': 4000
                    }
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=60
                )
            else:
                return {'error': f'Unknown provider: {provider}'}
            
            if response.status_code == 200:
                # Try to parse JSON - catch decode errors that occur when response.content is None
                # The error "decoding to str: need a bytes-like object, NoneType found" happens
                # when response.json() internally calls response.text which tries to decode None
                try:
                    result = response.json()
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    # Check if this is the specific decode error we're trying to fix
                    if 'decoding to str' in error_msg or 'NoneType' in error_msg or 'bytes-like object' in error_msg:
                        logger.error(f"LLM response decode error (content is None): {error_type}: {error_msg}")
                        return {'error': 'LLM provider returned empty or invalid response (content is None)'}
                    logger.error(f"Failed to parse JSON response: {error_type}: {error_msg}, response status: {response.status_code}")
                    return {'error': f'Invalid JSON response from LLM provider: {error_msg}'}
                
                if provider == 'openai':
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if not content:
                        return {'error': 'Empty response from OpenAI'}
                    return {'content': content}
                elif provider == 'ollama':
                    content = result.get('message', {}).get('content', '')
                    if not content:
                        return {'error': 'Empty response from Ollama'}
                    return {'content': content}
            else:
                # Safely get error text without triggering decode errors
                try:
                    if hasattr(response, 'text') and response.text is not None:
                        error_text = str(response.text)
                    else:
                        error_text = f'HTTP {response.status_code}'
                except Exception as e:
                    error_text = f'HTTP {response.status_code} (error getting response text: {str(e)})'
                return {'error': f'API request failed: {response.status_code} - {error_text}'}
                
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return {'error': str(e)}

