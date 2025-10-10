"""
Planning LLM Module

Contains LLM service and utility functions extracted from planning.py
"""

import logging
import json
import requests
import re

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self):
        self.providers = {
            'openai': {
                'name': 'OpenAI',
                'base_url': 'https://api.openai.com/v1',
                'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
            },
            'ollama': {
                'name': 'Ollama',
                'base_url': 'http://localhost:11434',
                'models': ['llama2', 'codellama', 'mistral']
            }
        }
    
    def get_available_models(self, provider='openai'):
        """Get available models for a provider."""
        try:
            if provider == 'ollama':
                response = requests.get(f"{self.providers[provider]['base_url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = [model['name'] for model in response.json().get('models', [])]
                    return models
            return self.providers.get(provider, {}).get('models', [])
        except Exception as e:
            logger.error(f"Error getting models for {provider}: {e}")
            return []
    
    def execute_llm_request(self, provider, model, messages, api_key=None, max_tokens=2000):
        """Execute LLM request."""
        try:
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': max_tokens
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
                        'num_predict': max_tokens
                    }
                }
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=120
                )
            else:
                return {'error': f'Unknown provider: {provider}'}
            
            if response.status_code == 200:
                result = response.json()
                if provider == 'openai':
                    return {'content': result['choices'][0]['message']['content']}
                elif provider == 'ollama':
                    return {'content': result['message']['content']}
            else:
                return {'error': f'API request failed: {response.status_code} - {response.text}'}
                
        except Exception as e:
            logger.error(f"Error executing LLM request: {e}")
            return {'error': str(e)}


def parse_brainstorm_topics(content):
    """Enhanced topic parsing with validation and categorization"""
    topics = []
    
    # Step 1: Try JSON parsing (expected format)
    try:
        # Clean up the content to extract JSON
        content_clean = content.strip()
        
        # Find JSON array boundaries
        start_idx = content_clean.find('[')
        end_idx = content_clean.rfind(']')
        
        if start_idx != -1 and end_idx != -1:
            json_str = content_clean[start_idx:end_idx + 1]
            parsed_data = json.loads(json_str)
        elif start_idx != -1:
            # JSON starts but doesn't end - try to fix truncated JSON
            json_str = content_clean[start_idx:]
            # Try to find the last complete object and close the array
            last_brace = json_str.rfind('}')
            if last_brace != -1:
                json_str = json_str[:last_brace + 1] + ']'
                try:
                    parsed_data = json.loads(json_str)
                except json.JSONDecodeError:
                    parsed_data = None
            else:
                parsed_data = None
        else:
            parsed_data = None
            
        if parsed_data and isinstance(parsed_data, list):
            for item in parsed_data:
                if isinstance(item, dict):
                    topic = {
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'category': item.get('category', 'general'),
                        'word_count': item.get('word_count', 0)
                    }
                    topics.append(topic)
                elif isinstance(item, str):
                    topics.append({
                        'title': item,
                        'description': '',
                        'category': 'general',
                        'word_count': len(item.split())
                    })
            return topics
    except json.JSONDecodeError:
        pass
    except Exception:
        pass
    
    # Step 2: Fallback to line-by-line parsing
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('*'):
            # Extract idea code if present
            idea_match = re.search(r'\{IDEA\d+\}', line)
            if idea_match:
                title = line.replace(idea_match.group(), '').strip()
                topics.append({
                    'title': f"{idea_match.group()} {title}",
                    'description': '',
                    'category': 'general',
                    'word_count': len(title.split())
                })
            elif len(line) > 10:  # Only include substantial lines
                topics.append({
                    'title': line,
                    'description': '',
                    'category': 'general',
                    'word_count': len(line.split())
                })
    
    return topics
