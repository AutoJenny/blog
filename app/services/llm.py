import httpx
import logging
from flask import current_app
from app.models import LLMConfig
import re
import json


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

    def execute_action(self, action, fields: dict, post_id: int = None):
        """Execute an LLM action with the given fields dict.
        Args:
            action: LLMAction instance to execute
            fields: dict of all fields for prompt substitution (should include 'input')
            post_id: Optional post ID to associate with the action history
        Returns:
            dict containing the response and model used
        """
        try:
            # Process the template
            prompt = action.process_template(fields)
            # Generate the response
            result = self.generate(prompt, model_name=action.llm_model)
            # Create history record if post_id provided
            if post_id:
                from app.models import LLMActionHistory
                from app import db
                history = LLMActionHistory(
                    action_id=action.id,
                    post_id=post_id,
                    input_text=fields.get('input', ''),
                    output_text=result['response'],
                    status='success'
                )
                db.session.add(history)
                db.session.commit()
            return result
        except Exception as e:
            # Log error and create failed history record if post_id provided
            current_app.logger.error(f"Error executing LLM action: {str(e)}")
            if post_id:
                from app.models import LLMActionHistory
                from app import db
                history = LLMActionHistory(
                    action_id=action.id,
                    post_id=post_id,
                    input_text=fields.get('input', ''),
                    status='error',
                    error_message=str(e)
                )
                db.session.add(history)
                db.session.commit()
            raise

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
            current_app.logger.info(f"[OLLAMA] Checking if model {model} is loaded...")
            ps_response = httpx.get(f"{base_url}/api/ps", timeout=5.0)
            ps_response.raise_for_status()
            loaded_models = [m["name"] for m in ps_response.json().get("models", [])]
            
            # If model not loaded, try to load it
            if model not in loaded_models:
                current_app.logger.info(f"[OLLAMA] Model {model} not loaded, attempting to load...")
                try:
                    load_response = httpx.post(
                        f"{base_url}/api/generate",
                        json={"model": model, "prompt": "", "stream": False},
                        timeout=60.0  # Increased timeout for model loading
                    )
                    load_response.raise_for_status()
                    current_app.logger.info(f"[OLLAMA] Model {model} loaded successfully")
                except httpx.TimeoutException:
                    current_app.logger.warning(f"[OLLAMA] Timeout while loading model {model}")
                    # Continue anyway - the model might still be loading in the background
                except Exception as e:
                    current_app.logger.error(f"[OLLAMA] Error loading model {model}: {str(e)}")
                    # Continue anyway - the model might still work

        except httpx.TimeoutException:
            current_app.logger.warning(f"[OLLAMA] Timeout while checking model {model} status")
            # Continue anyway - the model might still work
        except Exception as e:
            current_app.logger.error(f"[OLLAMA] Error checking model status: {str(e)}")
            # Continue anyway - the model might still work

        # Now try to generate
        url = f"{base_url}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        # Log the exact request being sent
        current_app.logger.info(f"[OLLAMA] Sending request to {url}")
        current_app.logger.info(f"[OLLAMA] Request data:\n{json.dumps(data, indent=2)}")
        
        try:
            current_app.logger.info(f"[OLLAMA] Generating response with model {model}...")
            response = httpx.post(url, json=data, timeout=60.0)
            response.raise_for_status()
            
            # Log the raw response
            current_app.logger.info(f"[OLLAMA] Raw response:\n{json.dumps(response.json(), indent=2)}")
            
            current_app.logger.info(f"[OLLAMA] Successfully generated response with model {model}")
            return {"response": response.json()["response"], "model_used": model}
        except httpx.TimeoutException:
            current_app.logger.error(f"[OLLAMA] Timeout during generation with model {model}")
            raise RuntimeError(
                f"LLM request timed out after 60 seconds. Model {model} may still be loading - "
                "please wait a moment and try again. If this persists, try preloading the model "
                "or using a different model."
            )
        except httpx.RequestError as e:
            current_app.logger.error(f"[OLLAMA] Connection error during generation with model {model}: {str(e)}")
            raise RuntimeError(
                f"Could not connect to LLM backend ({str(e)}). Please check that Ollama "
                "is running and accessible at {base_url}"
            )
        except Exception as e:
            current_app.logger.error(f"[OLLAMA] Unexpected error during generation with model {model}: {str(e)}")
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

    def generate_chat(self, messages, model_name=None, temperature=0.7, max_tokens=1000):
        """Generate text using configured LLM with chat-style messages."""
        if not model_name:
            model_name = self.config.model_name
            
        logger.info(f"Generating chat with model: {model_name}, temperature: {temperature}, max_tokens: {max_tokens}")

        if self.config.provider_type == "ollama":
            return self._generate_ollama_chat(messages, model_name, temperature, max_tokens)
        elif self.config.provider_type == "openai":
            return self._generate_openai_chat(messages, model_name, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider type: {self.config.provider_type}")

    def _generate_ollama_chat(self, messages, model_name, temperature=0.7, max_tokens=1000):
        """Generate text using Ollama with chat-style messages."""
        try:
            # Convert messages to a more explicit chat format
            prompt_parts = []
            for msg in messages:
                if msg['role'] == 'system':
                    prompt_parts.append(f"<system>\n{msg['content']}\n</system>")
                elif msg['role'] == 'user':
                    prompt_parts.append(f"<user>\n{msg['content']}\n</user>")
                elif msg['role'] == 'assistant':
                    prompt_parts.append(f"<assistant>\n{msg['content']}\n</assistant>")
            
            # Add final instruction to respond as assistant
            prompt_parts.append("<assistant>\nI will now provide my analysis:")
            
            # Join with clear separators
            prompt = "\n\n".join(prompt_parts)
            
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            logger.debug(f"Sending request to Ollama: {request_data}")
            
            response = httpx.post(
                f"{self.config.api_base}/api/generate",
                json=request_data,
                timeout=60.0,
            )
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
            
        except Exception as e:
            logger.exception(f"Error generating with Ollama: {str(e)}")
            raise

    def _generate_openai_chat(self, messages, model_name, temperature=0.7, max_tokens=1000):
        """Generate text using OpenAI with chat-style messages."""
        try:
            import openai
            client = openai.OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {str(e)}")
            raise

def execute_llm_request(request_data):
    """Execute an LLM request with the given parameters."""
    try:
        service = LLMService()
        
        # Log the incoming request
        logger.info(f"[LLM SERVICE] Received request data: {request_data}")
        
        # Get the prompt and input
        prompt_template = request_data.get('prompt', '').strip()
        input_text = request_data.get('input', '').strip()
        
        logger.info(f"[LLM SERVICE] Raw prompt template: '{prompt_template}'")
        logger.info(f"[LLM SERVICE] Raw input text: '{input_text}'")
        
        # Combine them in a way that makes it clear the input is the topic
        combined_prompt = (
            f"Here is your task: {prompt_template}\n\n"
            f"The topic you should write about is: {input_text}\n\n"
            f"Please write your response now, making sure to write about the topic provided."
        )
        
        logger.info(f"[LLM SERVICE] Combined prompt: '{combined_prompt}'")
        
        # Generate the output
        logger.info(f"[LLM SERVICE] Generating with model: {request_data.get('model_name')}")
        result = service.generate(
            combined_prompt,
            model_name=request_data.get('model_name'),
            temperature=request_data.get('temperature', 0.7),
            max_tokens=request_data.get('max_tokens', 2000)
        )
        
        if not result or not result.get('response'):
            logger.error("[LLM SERVICE] Empty response from generate()")
            return {'error': 'No output generated by the LLM service'}
            
        logger.info(f"[LLM SERVICE] Generated response: '{result['response'][:100]}...'")
        
        # Return in the format expected by the frontend
        return {
            'model_used': result.get('model_used', request_data.get('model_name')),
            'response': result['response']
        }
        
    except Exception as e:
        logger.exception("[LLM SERVICE] Error executing request")
        return {'error': str(e)}
