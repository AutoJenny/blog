"""
LLM Service Module

Service for interacting with LLM providers including OpenAI and Ollama.
"""

import requests
import logging

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
    
    def execute_llm_request(self, provider, model, messages, api_key=None, intercept_context=None):
        """Execute LLM request with message interception capability."""
        try:
            # STEP 1: Store the exact message structure in database
            if intercept_context:
                intercepted_message = self._format_intercepted_message(provider, model, messages, api_key)
                self._store_intercepted_message(intercepted_message, intercept_context)
                # Store the raw messages array as JSON for retrieval
                self._store_raw_messages(messages, intercept_context)
                # Store the complete API request data
                self._store_complete_api_request(provider, model, messages, api_key, intercept_context)
            
            # STEP 2: Retrieve the stored messages to ensure we send exactly what was stored
            if intercept_context:
                messages = self._retrieve_raw_messages(intercept_context) or messages
            
            # STEP 3: Validate intercept_context is provided
            if not intercept_context or not intercept_context.get('post_id') or not intercept_context.get('section_id'):
                logger.error("intercept_context with valid post_id and section_id is required")
                return {'error': 'intercept_context required'}
            
            if provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
                
                # Store the exact raw request that will be sent
                self._store_raw_http_request('POST', f"{self.providers[provider]['base_url']}/chat/completions", headers, data, intercept_context)
                
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
                
                # Store the exact raw request that will be sent
                self._store_raw_http_request('POST', f"{self.providers[provider]['base_url']}/api/chat", {'Content-Type': 'application/json'}, data, intercept_context)
                
                response = requests.post(
                    f"{self.providers[provider]['base_url']}/api/chat",
                    json=data,
                    timeout=60
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
    
    def _format_intercepted_message(self, provider, model, messages, api_key):
        """Format the intercepted message for storage and display."""
        formatted_message = f"PROVIDER: {provider.upper()}\n"
        formatted_message += f"MODEL: {model}\n"
        formatted_message += f"API_KEY: {'N/A' if not api_key else (api_key[:10] + '...' + api_key[-4:] if len(api_key) > 14 else api_key)}\n\n"
        
        formatted_message += "MESSAGES SENT TO LLM:\n"
        formatted_message += "=" * 50 + "\n"
        
        for i, message in enumerate(messages):
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            formatted_message += f"\n[{i+1}] ROLE: {role.upper()}\n"
            formatted_message += f"CONTENT:\n{content}\n"
            formatted_message += "-" * 30 + "\n"
        
        return formatted_message
    
    def _store_intercepted_message(self, intercepted_message, context):
        """Store the intercepted message in database."""
        try:
            from config.database import db_manager
            
            post_id = context.get('post_id')
            section_id = context.get('section_id')
            
            # Section ID must be numeric - no string ID handling
            if not isinstance(section_id, int) and not (isinstance(section_id, str) and section_id.isdigit()):
                logger.error(f"Invalid section_id: {section_id}. Must be numeric.")
                return
            
            section_id = int(section_id)
            
            with db_manager.get_cursor() as cursor:
                # Store in a new table for intercepted messages
                cursor.execute("""
                    INSERT INTO llm_message_intercepts 
                    (post_id, section_id, intercepted_message, created_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (post_id, section_id) 
                    DO UPDATE SET 
                        intercepted_message = EXCLUDED.intercepted_message,
                        created_at = EXCLUDED.created_at
                """, (post_id, section_id, intercepted_message))
                
                cursor.connection.commit()
                logger.info(f"Stored intercepted LLM message for post {post_id}, section {section_id}")
                
        except Exception as e:
            logger.error(f"Error storing intercepted message: {e}")
    
    def get_intercepted_message(self, post_id, section_id):
        """Retrieve the most recent intercepted message for a post/section."""
        try:
            from config.database import db_manager
            
            # Section ID must be numeric - no string ID handling
            if not isinstance(section_id, int) and not (isinstance(section_id, str) and section_id.isdigit()):
                logger.error(f"Invalid section_id: {section_id}. Must be numeric.")
                return None
            
            section_id = int(section_id)
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT intercepted_message, raw_messages, complete_api_request, raw_http_request, created_at
                    FROM llm_message_intercepts 
                    WHERE post_id = %s AND section_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (post_id, section_id))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'message': result['intercepted_message'],
                        'raw_messages': result['raw_messages'],
                        'complete_api_request': result['complete_api_request'],
                        'raw_http_request': result['raw_http_request'],
                        'created_at': result['created_at']
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving intercepted message: {e}")
            return None
    
    def _store_raw_messages(self, messages, context):
        """Store the raw messages array as JSON for exact retrieval."""
        try:
            from config.database import db_manager
            import json
            
            post_id = context.get('post_id')
            section_id = context.get('section_id')
            
            # Section ID must be numeric
            if not isinstance(section_id, int) and not (isinstance(section_id, str) and section_id.isdigit()):
                logger.error(f"Invalid section_id: {section_id}. Must be numeric.")
                return
            
            section_id = int(section_id)
            
            # Serialize messages to JSON
            messages_json = json.dumps(messages)
            
            with db_manager.get_cursor() as cursor:
                # Update the existing row to add raw_messages column
                cursor.execute("""
                    UPDATE llm_message_intercepts
                    SET raw_messages = %s
                    WHERE post_id = %s AND section_id = %s
                """, (messages_json, post_id, section_id))
                
                cursor.connection.commit()
                logger.info(f"Stored raw messages for post {post_id}, section {section_id}")
                
        except Exception as e:
            logger.error(f"Error storing raw messages: {e}")
    
    def _retrieve_raw_messages(self, context):
        """Retrieve the stored raw messages array."""
        try:
            from config.database import db_manager
            import json
            
            post_id = context.get('post_id')
            section_id = context.get('section_id')
            
            # Section ID must be numeric
            if not isinstance(section_id, int) and not (isinstance(section_id, str) and section_id.isdigit()):
                logger.error(f"Invalid section_id: {section_id}. Must be numeric.")
                return None
            
            section_id = int(section_id)
            
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT raw_messages
                    FROM llm_message_intercepts 
                    WHERE post_id = %s AND section_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (post_id, section_id))
                
                result = cursor.fetchone()
                if result and result['raw_messages']:
                    # raw_messages is already a Python object (JSONB), no need to parse
                    return result['raw_messages']
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving raw messages: {e}")
            return None
    
    def _store_complete_api_request(self, provider, model, messages, api_key, context):
        """Store the complete API request data that gets sent to the LLM."""
        try:
            from config.database import db_manager
            import json
            
            post_id = context.get('post_id')
            section_id = context.get('section_id')
            
            # Section ID must be numeric
            if not isinstance(section_id, int) and not (isinstance(section_id, str) and section_id.isdigit()):
                logger.error(f"Invalid section_id: {section_id}. Must be numeric.")
                return
            
            section_id = int(section_id)
            
            # Build the complete API request data
            if provider == 'openai':
                api_request = {
                    "url": f"{self.providers[provider]['base_url']}/chat/completions",
                    "headers": {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    "data": {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                }
            elif provider == 'ollama':
                api_request = {
                    "url": f"{self.providers[provider]['base_url']}/api/chat",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "data": {
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": 4000
                        }
                    }
                }
            else:
                logger.error(f"Unknown provider: {provider}")
                return
            
            # Serialize to JSON
            api_request_json = json.dumps(api_request, indent=2)
            
            with db_manager.get_cursor() as cursor:
                # Update the existing row to add complete_api_request column
                cursor.execute("""
                    UPDATE llm_message_intercepts
                    SET complete_api_request = %s
                    WHERE post_id = %s AND section_id = %s
                """, (api_request_json, post_id, section_id))
                
                cursor.connection.commit()
                logger.info(f"Stored complete API request for post {post_id}, section {section_id}")
                
        except Exception as e:
            logger.error(f"Error storing complete API request: {e}")
    
    def _store_raw_http_request(self, method, url, headers, data, context):
        """Store the exact raw HTTP request that gets sent to the LLM."""
        try:
            from config.database import db_manager
            import json
            
            post_id = context.get('post_id')
            section_id = context.get('section_id')
            
            # Section ID must be numeric
            if not isinstance(section_id, int) and not (isinstance(section_id, str) and section_id.isdigit()):
                logger.error(f"Invalid section_id: {section_id}. Must be numeric.")
                return
            
            section_id = int(section_id)
            
            # Build the exact raw HTTP request
            raw_request = f"{method} {url} HTTP/1.1\n"
            for header_name, header_value in headers.items():
                raw_request += f"{header_name}: {header_value}\n"
            raw_request += "\n"
            raw_request += json.dumps(data, indent=2)
            
            with db_manager.get_cursor() as cursor:
                # Update the existing row to add raw_http_request column
                cursor.execute("""
                    UPDATE llm_message_intercepts
                    SET raw_http_request = %s
                    WHERE post_id = %s AND section_id = %s
                """, (raw_request, post_id, section_id))
                
                cursor.connection.commit()
                logger.info(f"Stored raw HTTP request for post {post_id}, section {section_id}")
                
        except Exception as e:
            logger.error(f"Error storing raw HTTP request: {e}")


# Initialize LLM service instance
llm_service = LLMService()
