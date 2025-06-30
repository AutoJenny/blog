"""Service for interacting with LLM providers."""

import httpx
import logging
import re
from flask import current_app
from datetime import datetime
from jinja2 import Template
import psycopg2
import psycopg2.extras
import requests
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
# All ORM model imports removed. Use direct SQL via psycopg2 for any DB access.

llm_outgoing_logger = logging.getLogger('llm_outgoing')
llm_outgoing_logger.setLevel(logging.INFO)
if not llm_outgoing_logger.handlers:
    handler = logging.FileHandler('llm_outgoing.log')
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    llm_outgoing_logger.addHandler(handler)

def execute_request(request_data: Dict[str, Any], provider: str = 'ollama', model: str = 'llama3.1:70b') -> Optional[str]:
    """Execute an LLM request."""
    current_app.logger.info(f"[LLM Request] Provider: {provider}, Model: {model}")
    current_app.logger.info(f"[LLM Request] Prompt: {request_data.get('prompt')}")
    
    # Initialize LLM service and call the real LLM
    llm_service = LLMService()
    return llm_service.generate(
        prompt=request_data.get('prompt', ''),
        model_name=model,
        temperature=request_data.get('temperature', 0.7),
        max_tokens=request_data.get('max_tokens', 1000)
    )

def execute_llm_request(provider, model, prompt, temperature=0.7, max_tokens=1000, api_key=None, api_endpoint=None):
    """Execute an LLM request with the given parameters."""
    # Initialize LLM service and call the real LLM
    llm_service = LLMService()
    return llm_service.generate(
        prompt=prompt,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

def assemble_prompt_from_parts(action, fields: dict):
    """
    Assemble a prompt or message list from all prompt parts for an action, ordered.
    For OpenAI: returns a list of {role, content} dicts.
    For Ollama: returns a single concatenated string.
    """
    prompt_parts = (
        LLMActionPromptPart.query.filter_by(action_id=action['id'])
        .order_by(LLMActionPromptPart.order)
        .all()
    )
    messages = []
    for part_link in prompt_parts:
        part = part_link.prompt_part
        # Render with Jinja2
        try:
            content = Template(part.content).render(**fields)
        except Exception as e:
            logger.error(f"Error rendering prompt part {part.id}: {e}")
            content = part.content
        # For OpenAI, use role; for Ollama, just concatenate
        if part.type in ('system', 'user', 'assistant'):
            messages.append({'role': part.type, 'content': content})
        else:
            # For style/instructions/other, treat as user message
            messages.append({'role': 'user', 'content': content})
    # For Ollama, concatenate all content
    ollama_prompt = '\n\n'.join([m['content'] for m in messages])
    return {'openai': messages, 'ollama': ollama_prompt}

def parse_tagged_prompt_to_messages(prompt_template: str, fields: dict) -> dict:
    """
    Parse a tagged prompt template into structured messages (for chat LLMs) and a canonical prompt string (for single-prompt LLMs).
    Returns: { 'messages': [...], 'prompt': '...' }
    """
    current_app.logger.debug(f"[DEBUG] Parsing tagged prompt: {prompt_template}")
    # Replace [data:FIELDNAME] with the actual input, if present
    def replace_data_tags(text):
        def repl(match):
            key = match.group(1)
            return str(fields.get(key, f"[{key}]") if fields else f"[{key}]")
        return re.sub(r'\[data:([a-zA-Z0-9_]+)\]', repl, text)

    # Find all [role: TAG] or [role] blocks
    tag_pattern = re.compile(r'\[(system|user|assistant)(?::\s*([A-Z_]+))?\]\s*([^\[]+)', re.IGNORECASE)
    matches = tag_pattern.findall(prompt_template)
    current_app.logger.debug(f"[DEBUG] Tag matches: {matches}")
    # Group content by role
    role_contents = {'system': [], 'user': [], 'assistant': []}
    for role, tag, content in matches:
        role = role.lower()
        content = replace_data_tags(content.strip())
        role_contents.setdefault(role, []).append(content)
    # Compose messages for chat LLMs
    messages = []
    for role in ('system', 'user', 'assistant'):
        if role_contents[role]:
            messages.append({'role': role, 'content': ' '.join(role_contents[role])})
    # Compose canonical prompt string for single-prompt LLMs
    prompt_lines = []
    if role_contents['system']:
        prompt_lines.append(' '.join(role_contents['system']))
    if role_contents['user']:
        prompt_lines.append('Task: ' + ' '.join(role_contents['user']))
    if 'input' in fields:
        prompt_lines.append('Input: ' + str(fields['input']))
    prompt = '\n'.join(prompt_lines)
    current_app.logger.debug(f"[DEBUG] Parsed messages: {messages}")
    current_app.logger.debug(f"[DEBUG] Parsed prompt: {prompt}")
    return {'messages': messages, 'prompt': prompt}

def modular_prompt_to_canonical(prompt_json, fields: dict) -> dict:
    """
    Convert a modular prompt array (list of parts) and runtime fields into a canonical prompt string and message list.
    Returns: { 'messages': [...], 'prompt': '...' }
    """
    import json as _json
    if isinstance(prompt_json, str):
        try:
            prompt_json = _json.loads(prompt_json)
        except Exception:
            return {'messages': [], 'prompt': ''}
    if isinstance(prompt_json, dict):
        prompt_json = [prompt_json]

    # Collect all content parts
    prompt_parts = []
    input_val = fields.get('input', '')
    
    # Process all parts in order
    for part in prompt_json:
        content = part.get('content', '').strip()
        if not content:
            continue
        prompt_parts.append(content)
        
        # If this is a data part with content, use it as default input
        if part.get('type') == 'data' and content:
            input_val = content

    # Compose the final prompt string
    prompt = '\n\n'.join(prompt_parts)
    if input_val:
        prompt += f"\n\nData for this operation as follows: {input_val}"

    # Compose messages for chat LLMs
    messages = []
    if prompt_parts:
        messages.append({'role': 'system', 'content': prompt_parts[0]})
        if len(prompt_parts) > 1:
            messages.append({'role': 'user', 'content': '\n\n'.join(prompt_parts[1:])})
        if input_val:
            messages.append({'role': 'user', 'content': str(input_val)})

    # --- DEBUG LOGGING ---
    logger = logging.getLogger(__name__)
    logger.error(f"[DEBUG] modular_prompt_to_canonical prompt_parts: {prompt_parts}")
    logger.error(f"[DEBUG] modular_prompt_to_canonical input_val: {input_val}")
    logger.error(f"[DEBUG] modular_prompt_to_canonical final prompt: {prompt}")

    return {'messages': messages, 'prompt': prompt}

def log_llm_outgoing(payload: dict) -> str:
    prompt = payload.get('prompt', '')
    llm_outgoing_logger.info(f"LLM PAYLOAD: {payload}")
    return prompt

class LLMService:
    """Service for interacting with LLM providers."""

    def __init__(self):
        """Initialize the LLM service."""
        self.ollama_url = current_app.config.get("OLLAMA_API_URL", "http://localhost:11434")
        self.openai_api_key = current_app.config.get("OPENAI_API_KEY")
        self.default_model = current_app.config.get("DEFAULT_LLM_MODEL", "mistral")

    def plan_structure(self, title, idea, facts):
        """Plan the structure of a blog post using LLM."""
        prompt = f"""You are a professional blog post planner. Given the following blog post details, create a structured outline with 7 sections.

Title: {title}
Basic Idea: {idea}
Key Facts to Include: {', '.join(facts)}

Create 7 sections that will form a coherent, engaging blog post. Each section should:
1. Have a clear, descriptive title
2. Include a brief description of what will be covered
3. List specific ideas to include
4. List specific facts to include

Format your response as a JSON array of section objects, each with:
- title: string
- description: string
- ideas: array of strings
- facts: array of strings

Example format:
[
  {{
    "title": "Introduction",
    "description": "Brief overview of the topic and why it matters",
    "ideas": ["Hook the reader", "Present the main thesis"],
    "facts": ["Key statistic", "Relevant quote"]
  }},
  ...
]"""

        try:
            # Generate the structure using the LLM
            response = self.generate(
                prompt,
                model_name=self.default_model,
                temperature=0.7,
                max_tokens=2000
            )

            # Parse the response as JSON
            import json
            sections = json.loads(response)

            # Validate the response format
            if not isinstance(sections, list):
                raise ValueError("LLM response is not a list of sections")

            for section in sections:
                if not all(k in section for k in ['title', 'description', 'ideas', 'facts']):
                    raise ValueError("Section missing required fields")

            return sections

        except Exception as e:
            current_app.logger.error(f"Error planning structure: {str(e)}")
            raise

    def generate(self, prompt, model_name=None, temperature=0.7, max_tokens=1000, timeout=60):
        """Generate text using configured LLM, supporting both OpenAI (messages) and Ollama (string)."""
        if not model_name:
            model_name = self.default_model
        logger.info(f"Generating with model: {model_name}, temperature: {temperature}, max_tokens: {max_tokens}, timeout: {timeout}")
        if self.ollama_url:
            return self._generate_ollama(prompt, model_name, temperature, max_tokens, timeout)
        elif self.openai_api_key:
            return self._generate_openai(prompt, model_name, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider type: {self.ollama_url}")

    def _generate_ollama(self, prompt, model_name, temperature=0.7, max_tokens=1000, timeout=60):
        """Generate text using Ollama."""
        try:
            # Format request JSON consistently
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "temperature": float(temperature),  # Ensure temperature is float
                "max_tokens": int(max_tokens),      # Ensure max_tokens is int
                "stream": False  # Ensure we get a complete response
            }
            logger.debug(f"[REQUESTS] Sending request to Ollama: {request_data}")
            if not self.ollama_url:
                raise ValueError("Ollama API URL not set on LLMService")
            # Use requests instead of httpx
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=timeout or 60
            )
            logger.debug(f"[REQUESTS] Request headers: {response.request.headers}")
            logger.debug(f"[REQUESTS] Request body: {response.request.body}")
            logger.debug(f"[REQUESTS] Raw response: {response.text}")
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"Received response from Ollama: {response_data}")
            # Handle both response formats
            if "response" in response_data:
                return response_data["response"]
            elif isinstance(response_data, dict) and "model_used" in response_data and "response" in response_data:
                return response_data["response"]
            else:
                logger.error(f"Unexpected response format from Ollama: {response_data}")
                raise ValueError("Unexpected response format from Ollama")
        except requests.Timeout:
            logger.error(f"Timeout while generating with Ollama (model: {model_name})")
            raise TimeoutError("Request to Ollama timed out")
        except requests.RequestException as e:
            logger.error(f"HTTP error while generating with Ollama: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Error generating with Ollama: {str(e)}")
            raise

    def _generate_openai(self, prompt, model_name, temperature=0.7, max_tokens=1000):
        """Generate text using OpenAI (stubbed for testing)."""
        # Return a dummy response for testing if no API key is set
        return "[DUMMY OPENAI RESPONSE]"

    def execute_action(self, action, fields: dict, post_id=None, model_name=None):
        model = None
        if model_name:
            model = model_name
        elif action['llm_model']:
            model = action['llm_model']
        else:
            raise ValueError(f"LLM model not set on action {action['id']}")
        # Use self.ollama_url and self.openai_api_key as set by the caller.
        # --- NEW: Transform modular prompt_json to canonical prompt/messages ---
        prompt_json = action.get('prompt_json')
        if prompt_json is not None:
            parsed = modular_prompt_to_canonical(prompt_json, fields)
        else:
            # Fallback for legacy actions: use prompt_template string
            prompt_template = action.get('prompt_template', '')
            parsed = parse_tagged_prompt_to_messages(prompt_template, fields)
        current_app.logger.debug(f"[DEBUG] LLMService.execute_action parsed: {parsed}")
        input_field = action.get('input_field') or 'input'
        output_field = action.get('output_field') or 'output'
        llm_payload = None
        if self.openai_api_key:
            llm_payload = {
                'model': model,
                'messages': parsed['messages'],
                'temperature': action['temperature'],
                'max_tokens': action['max_tokens']
            }
            result = self.generate(parsed['messages'], model_name=model, temperature=action['temperature'], max_tokens=action['max_tokens'])
        elif self.ollama_url:
            llm_payload = {
                'model': model,
                'prompt': parsed['prompt'],
                'temperature': action['temperature'],
                'max_tokens': action['max_tokens'],
                'stream': False
            }
            result = self.generate(parsed['prompt'], model_name=model, temperature=action['temperature'], max_tokens=action['max_tokens'])
        else:
            raise ValueError(f"Unsupported provider type: {self.ollama_url}")
        if isinstance(result, dict) and 'output' in result:
            result = {output_field: result['output'], **{k: v for k, v in result.items() if k != 'output'}}
        elif isinstance(result, str):
            result = {output_field: result}
        def make_json_safe(obj):
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_safe(i) for i in obj]
            return obj
        # Always include the full LLM payload for debugging/transparency
        result['llm_payload'] = llm_payload
        return make_json_safe(result)

# Remove all ORM model usage below, stub out as needed for migration. 