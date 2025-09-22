from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras
import requests
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import preview blueprint
from preview import bp as preview_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_conn():
    """Get database connection."""
    return psycopg2.connect(app.config['DATABASE_URL'], connect_timeout=5)

class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(self, ollama_url=None, openai_api_key=None, default_model=None):
        """Initialize the LLM service."""
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.default_model = default_model or os.environ.get("DEFAULT_LLM_MODEL", "mistral")

    def generate(self, prompt, model_name=None, temperature=0.7, max_tokens=1000, timeout=60):
        """Generate text using configured LLM."""
        if not model_name:
            model_name = self.default_model
        logger.info(f"Generating with model: {model_name}, temperature: {temperature}, max_tokens: {max_tokens}")
        
        if self.ollama_url:
            return self._generate_ollama(prompt, model_name, temperature, max_tokens, timeout)
        elif self.openai_api_key:
            return self._generate_openai(prompt, model_name, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider type: {self.ollama_url}")

    def _generate_ollama(self, prompt, model_name, temperature=0.7, max_tokens=1000, timeout=60):
        """Generate text using Ollama."""
        try:
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
                "stream": False
            }
            logger.debug(f"Sending request to Ollama: {request_data}")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=timeout or 60
            )
            response.raise_for_status()
            response_data = response.json()
            
            if "response" in response_data:
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
        return "[DUMMY OPENAI RESPONSE]"

def execute_llm_request(provider, model, prompt, temperature=0.7, max_tokens=1000, api_key=None, api_endpoint=None):
    """Execute an LLM request with the given parameters."""
    llm_service = LLMService()
    return llm_service.generate(
        prompt=prompt,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

def modular_prompt_to_canonical(prompt_json, fields: dict) -> dict:
    """Convert a modular prompt array and runtime fields into a canonical prompt string and message list."""
    if isinstance(prompt_json, str):
        try:
            prompt_json = json.loads(prompt_json)
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

    return {'messages': messages, 'prompt': prompt}

def parse_tagged_prompt_to_messages(prompt_template: str, fields: dict) -> dict:
    """Parse a tagged prompt template into structured messages and a canonical prompt string."""
    import re
    
    # Replace [data:FIELDNAME] with the actual input
    def replace_data_tags(text):
        def repl(match):
            key = match.group(1)
            return str(fields.get(key, f"[{key}]") if fields else f"[{key}]")
        return re.sub(r'\[data:([a-zA-Z0-9_]+)\]', repl, text)

    # Find all [role: TAG] or [role] blocks
    tag_pattern = re.compile(r'\[(system|user|assistant)(?::\s*([A-Z_]+))?\]\s*([^\[]+)', re.IGNORECASE)
    matches = tag_pattern.findall(prompt_template)
    
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
    
    return {'messages': messages, 'prompt': prompt}

@app.route('/')
def index():
    """Main LLM Actions interface with context support."""
    # Get context parameters from request
    stage = request.args.get('stage', 'planning')
    substage = request.args.get('substage', 'idea')
    step = request.args.get('step', 'basic_idea')
    post_id = request.args.get('post_id', '1')
    step_id = request.args.get('step_id')
    
    # If step_id not provided, try to get it from database
    if not step_id:
        try:
            with get_db_conn() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                # Convert step name from URL format to database format (e.g., "author_first_drafts" -> "Author First Drafts")
                db_step_name = step.replace('_', ' ').title()
                
                cur.execute("""
                    SELECT ws.id as step_id
                    FROM workflow_stage_entity s
                    JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                    JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id
                    WHERE s.name ILIKE %s
                    AND ss.name ILIKE %s
                    AND ws.name ILIKE %s
                """, (stage, substage, db_step_name))
                result = cur.fetchone()
                if result:
                    step_id = result['step_id']
        except Exception as e:
            logger.warning(f"Could not get step_id: {str(e)}")
    
    # Pass context to template
    context = {
        'current_stage': stage,
        'current_substage': substage,
        'current_step': step,
        'current_post_id': post_id,
        'current_step_id': step_id
    }
    
    return render_template('index.html', **context)





@app.route('/test')
def test_page():
    """Test page for API functionality."""
    return app.send_static_file('test_api.html')

@app.route('/api/context', methods=['GET', 'POST'])
def context():
    """Handle context management."""
    if request.method == 'POST':
        data = request.get_json()
        # TODO: Save context to database
        return jsonify({'status': 'success', 'message': 'Context updated'})
    
    # Get context from database - no hardcoded values
    context_data = {
        'system_prompt': '',
        'persona': '',
        'additional_fields': []
    }
    return jsonify(context_data)

@app.route('/api/task', methods=['GET', 'POST'])
def task():
    """Handle task management."""
    if request.method == 'POST':
        data = request.get_json()
        # TODO: Save task to database
        return jsonify({'status': 'success', 'message': 'Task updated'})
    
    # Get task from database - no hardcoded values
    task_data = {
        'current_task': '',
        'task_history': []
    }
    return jsonify(task_data)

@app.route('/api/start-ollama', methods=['POST'])
def start_ollama():
    """Start Ollama service."""
    try:
        import subprocess
        import sys
        
        # Check if Ollama is already running
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.ok:
                return jsonify({
                    'status': 'success',
                    'message': 'Ollama is already running'
                })
        except:
            pass  # Ollama is not running, continue to start it
        
        # Try to start Ollama
        try:
            # Use subprocess to start Ollama in the background
            if sys.platform == 'darwin':  # macOS
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL,
                               start_new_session=True)
            else:  # Linux/Windows
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            # Wait a moment for Ollama to start
            import time
            time.sleep(3)
            
            # Check if Ollama started successfully
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                if response.ok:
                    return jsonify({
                        'status': 'success',
                        'message': 'Ollama started successfully'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'error': 'Ollama started but is not responding properly'
                    }), 500
            except requests.RequestException:
                return jsonify({
                    'status': 'error',
                    'error': 'Ollama started but is not responding. Please check if it\'s running properly.'
                }), 500
                
        except FileNotFoundError:
            return jsonify({
                'status': 'error',
                'error': 'Ollama is not installed. Please install Ollama first.'
            }), 404
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': f'Failed to start Ollama: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting Ollama: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/run-llm', methods=['POST'])
def run_llm():
    """Execute LLM action."""
    data = request.get_json()
    
    try:
        # Get LLM configuration from database
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT provider_type, model_name, api_base
                FROM llm_config
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            """)
            config = cur.fetchone()
            if not config:
                # Fallback to default configuration
                config = {
                    'provider_type': 'ollama',
                    'model_name': 'mistral',
                    'api_base': 'http://localhost:11434'
                }
        
        # Get section-specific context if section_id is provided
        section_id = data.get('section_id')
        section_context = ""
        if section_id:
            try:
                with get_db_conn() as conn:
                    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    cur.execute("""
                        SELECT section_heading, section_description, draft, ideas_to_include, facts_to_include
                        FROM post_section
                        WHERE id = %s
                    """, (section_id,))
                    section = cur.fetchone()
                    if section:
                        section_context = f"\n\nSection Context:\nHeading: {section['section_heading']}"
                        if section['section_description']:
                            section_context += f"\nDescription: {section['section_description']}"
                        if section['draft']:
                            section_context += f"\nCurrent Content: {section['draft']}"
                        if section['ideas_to_include']:
                            section_context += f"\nIdeas to Include: {section['ideas_to_include']}"
                        if section['facts_to_include']:
                            section_context += f"\nFacts to Include: {section['facts_to_include']}"
            except Exception as e:
                logger.error(f"Error getting section context: {str(e)}")
        
        # Construct prompt from context and task
        system_prompt = data.get('system_prompt', '')
        persona = data.get('persona', '')
        task = data.get('task', '')
        
        prompt = f"{system_prompt}\n\n{persona}\n\nTask: {task}{section_context}"
        
        # Call LLM
        llm_service = LLMService()
        result = llm_service.generate(
            prompt=prompt,
            model_name=config['model_name'],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Save output to database if post_id and output_field are provided
        post_id = data.get('post_id')
        output_field = data.get('output_field')
        
        if post_id and output_field:
            try:
                # Check if this is a section-specific field
                section_fields = [
                    'image_concepts', 'image_prompts', 'image_meta_descriptions',
                    'image_captions', 'ideas_to_include', 'facts_to_include',
                    'draft', 'polished', 'highlighting', 'watermarking', 'status'
                ]
                
                if output_field in section_fields and section_id:
                    # Save to specific section via sections API
                    sections_api_url = f"http://localhost:5003/api/sections/{section_id}"
                    update_data = {output_field: result}
                    response = requests.put(sections_api_url, json=update_data, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Saved LLM output to {output_field} for section {section_id}")
                    else:
                        logger.error(f"Failed to save to sections API: {response.status_code} - {response.text}")
                else:
                    # Determine which table to save to based on stage/substage
                    stage = data.get('stage', '')
                    substage = data.get('substage', '')
                    
                    # Check if this is a post_info stage field that should go to post table
                    if stage == 'writing' and substage == 'post_info':
                        post_fields = ['title', 'subtitle', 'title_choices', 'summary']
                        if output_field in post_fields:
                            # Save to post table
                            with get_db_conn() as conn:
                                cur = conn.cursor()
                                cur.execute(f"""
                                    UPDATE post 
                                    SET {output_field} = %s
                                    WHERE id = %s
                                """, (result, post_id))
                                conn.commit()
                                logger.info(f"Saved LLM output to post.{output_field} for post {post_id}")
                        else:
                            # Save to post_development table
                            with get_db_conn() as conn:
                                cur = conn.cursor()
                                cur.execute("""
                                    SELECT id FROM post_development 
                                    WHERE post_id = %s
                                """, (post_id,))
                                
                                db_result = cur.fetchone()
                                if not db_result:
                                    # Create new record
                                    cur.execute(f"""
                                        INSERT INTO post_development (post_id, {output_field})
                                        VALUES (%s, %s)
                                    """, (post_id, result))
                                else:
                                    # Update existing record
                                    cur.execute(f"""
                                        UPDATE post_development 
                                        SET {output_field} = %s
                                        WHERE post_id = %s
                                    """, (result, post_id))
                                conn.commit()
                                logger.info(f"Saved LLM output to post_development.{output_field} for post {post_id}")
                    else:
                        # Default: save to post_development table
                        with get_db_conn() as conn:
                            cur = conn.cursor()
                            cur.execute("""
                                SELECT id FROM post_development 
                                WHERE post_id = %s
                            """, (post_id,))
                            
                            db_result = cur.fetchone()
                            if not db_result:
                                # Create new record
                                cur.execute(f"""
                                    INSERT INTO post_development (post_id, {output_field})
                                    VALUES (%s, %s)
                                """, (post_id, result))
                            else:
                                # Update existing record
                                cur.execute(f"""
                                    UPDATE post_development 
                                    SET {output_field} = %s
                                    WHERE post_id = %s
                                """, (result, post_id))
                            conn.commit()
                            logger.info(f"Saved LLM output to post_development.{output_field} for post {post_id}")
            except Exception as e:
                logger.error(f"Error saving LLM output to database: {str(e)}")
                # Continue even if save fails - still return the result
        
        return jsonify({
            'status': 'success',
            'result': result,
            'output': result
        })
        
    except requests.ConnectionError as e:
        logger.error(f"Connection error in run_llm: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'LLM service is not available. Please ensure Ollama is running on port 11434.',
            'details': 'Connection refused to localhost:11434'
        }), 503
    except requests.Timeout as e:
        logger.error(f"Timeout error in run_llm: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'LLM request timed out. Please try again.',
            'details': str(e)
        }), 408
    except Exception as e:
        logger.error(f"Error in run_llm: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/llm/config', methods=['GET'])
def get_llm_config():
    """Get current LLM configuration."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT provider_type, model_name, api_base, is_active
                FROM llm_config
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            """)
            config = cur.fetchone()
            
        if config:
            return jsonify({
                'provider_type': config['provider_type'],
                'model_name': config['model_name'],
                'api_base': config['api_base'],
                'is_active': config['is_active']
            })
        else:
            return jsonify({
                'provider_type': 'ollama',
                'model_name': 'mistral',
                'api_base': 'http://localhost:11434',
                'is_active': True
            })
    except Exception as e:
        logger.error(f"Error getting LLM config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/test', methods=['POST'])
def test_llm():
    """Test LLM connection."""
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'Hello, how are you?')
        model = data.get('model', 'mistral')
        
        llm_service = LLMService()
        result = llm_service.generate(
            prompt=prompt,
            model_name=model,
            temperature=0.7,
            max_tokens=100
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Connection successful',
            'response': result
        })
    except Exception as e:
        logger.error(f"Error testing LLM: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/providers', methods=['GET'])
def get_providers():
    """Get all LLM providers."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT id, name, type, api_url, description, created_at, updated_at
                FROM llm_provider
                ORDER BY id
            """)
            providers = cur.fetchall()
            
        return jsonify([dict(p) for p in providers])
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/models', methods=['GET'])
def get_models():
    """Get all LLM models."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT m.id, m.name, m.provider_id, m.description, m.strengths,
                       p.name as provider_name, p.type as provider_type
                FROM llm_model m
                JOIN llm_provider p ON p.id = m.provider_id
                ORDER BY m.name
            """)
            models = cur.fetchall()
            
        return jsonify([
            {
                'id': str(m['id']),
                'name': m['name'],
                'provider': m['provider_name'],
                'capabilities': [m['strengths']] if m['strengths'] else [],
                'description': m['description'],
                'provider_type': m['provider_type']
            } for m in models
        ])
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/actions', methods=['GET'])
def get_actions():
    """Get all TASK prompts organized exactly like workflow_prompts page."""
    try:
        # Use the same database connection as blog-core to get the correct data
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
        from db import get_db_conn as get_blog_core_db_conn
        
        with get_blog_core_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get ALL task prompts (not just linked ones) - this is the fix!
            cur.execute("""
                SELECT lp.id, lp.name, lp.description, 
                       COALESCE(lp.system_prompt, '') as system_prompt,
                       COALESCE(lp.prompt_text, '') as prompt_text,
                       wsp.step_id,
                       wse.name as step_name,
                       wse.sub_stage_id,
                       wsse.name as substage_name,
                       wsse.stage_id,
                       wstage.name as stage_name,
                       wstage.stage_order,
                       wsse.sub_stage_order,
                       wse.step_order
                FROM llm_prompt lp
                LEFT JOIN workflow_step_prompt wsp ON lp.id = wsp.task_prompt_id
                LEFT JOIN workflow_step_entity wse ON wsp.step_id = wse.id
                LEFT JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                LEFT JOIN workflow_stage_entity wstage ON wsse.stage_id = wstage.id
                WHERE lp.system_prompt IS NULL OR lp.system_prompt = ''
                ORDER BY lp.name
            """)
            task_prompts = cur.fetchall()

            # Get workflow stages and substages (EXACT same queries as workflow_prompts)
            cur.execute("""
                SELECT id, name, description, stage_order
                FROM workflow_stage_entity
                ORDER BY stage_order
            """)
            stages = cur.fetchall()

            cur.execute("""
                SELECT id, stage_id, name, description, sub_stage_order
                FROM workflow_sub_stage_entity
                ORDER BY stage_id, sub_stage_order
            """)
            substages = cur.fetchall()

            # Get all steps (EXACT same query as workflow_prompts)
            cur.execute("""
                SELECT id, name, sub_stage_id, step_order
                FROM workflow_step_entity
                ORDER BY step_order
            """)
            steps = cur.fetchall()

            # Organize task prompts by stage/substage/step (EXACT same logic as workflow_prompts)
            tasks_by_stage = {}
            unassigned_prompts = []
            
            for prompt in task_prompts:
                if prompt['step_id'] is None:
                    unassigned_prompts.append(prompt)
                else:
                    stage_id = prompt['stage_id']
                    substage_id = prompt['sub_stage_id']
                    step_id = prompt['step_id']
                    
                    if stage_id not in tasks_by_stage:
                        tasks_by_stage[stage_id] = {
                            'name': prompt['stage_name'],
                            'stage_order': next((s['stage_order'] for s in stages if s['id'] == stage_id), 0),
                            'substages': {}
                        }
                    
                    if substage_id not in tasks_by_stage[stage_id]['substages']:
                        tasks_by_stage[stage_id]['substages'][substage_id] = {
                            'name': prompt['substage_name'],
                            'sub_stage_order': next((ss['sub_stage_order'] for ss in substages if ss['id'] == substage_id), 0),
                            'steps': {}
                        }
                    
                    if step_id not in tasks_by_stage[stage_id]['substages'][substage_id]['steps']:
                        tasks_by_stage[stage_id]['substages'][substage_id]['steps'][step_id] = {
                            'name': prompt['step_name'],
                            'step_order': next((st['step_order'] for st in steps if st['id'] == step_id), 0),
                            'prompts': []
                        }
                    
                    tasks_by_stage[stage_id]['substages'][substage_id]['steps'][step_id]['prompts'].append(prompt)
            
            # Sort stages by stage_order, substages by sub_stage_order, and steps by step_order (EXACT same logic as workflow_prompts)
            sorted_tasks_by_stage = {}
            for stage_id in sorted(tasks_by_stage.keys(), key=lambda x: tasks_by_stage[x]['stage_order']):
                stage_data = tasks_by_stage[stage_id]
                sorted_substages = {}
                for substage_id in sorted(stage_data['substages'].keys(), key=lambda x: stage_data['substages'][x]['sub_stage_order']):
                    substage_data = stage_data['substages'][substage_id]
                    sorted_steps = {}
                    for step_id in sorted(substage_data['steps'].keys(), key=lambda x: substage_data['steps'][x]['step_order']):
                        sorted_steps[step_id] = substage_data['steps'][step_id]
                    sorted_substages[substage_id] = {
                        'name': substage_data['name'],
                        'steps': sorted_steps
                    }
                sorted_tasks_by_stage[stage_id] = {
                    'name': stage_data['name'],
                    'substages': sorted_substages
                }
            
            # Convert to flat list - show ALL prompts regardless of step assignment
            flat_prompts = []
            
            for prompt in task_prompts:
                if prompt['step_id'] is not None:
                    # Prompt is linked to a step
                    flat_prompts.append({
                        'id': prompt['id'],
                        'field_name': prompt['name'],
                        'prompt_template': prompt['prompt_text'],
                        'description': prompt['description'],
                        'created_at': prompt.get('created_at'),
                        'updated_at': prompt.get('updated_at'),
                        'step_id': prompt['step_id'],
                        'step_name': prompt['step_name'],
                        'substage_name': prompt['substage_name'],
                        'stage_name': prompt['stage_name'],
                        'group': f"{prompt['stage_name']} > {prompt['substage_name']} > {prompt['step_name']}"
                    })
                else:
                    # Prompt is not linked to any step - show it as available
                    flat_prompts.append({
                        'id': prompt['id'],
                        'field_name': prompt['name'],
                        'prompt_template': prompt['prompt_text'],
                        'description': prompt['description'],
                        'created_at': prompt.get('created_at'),
                        'updated_at': prompt.get('updated_at'),
                        'step_id': None,
                        'step_name': None,
                        'substage_name': None,
                        'stage_name': None,
                        'group': 'Available Prompts'
                    })
            
        return jsonify(flat_prompts)
    except Exception as e:
        logger.error(f"Error getting task prompts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/system-prompts', methods=['GET'])
def get_system_prompts():
    """Get all SYSTEM prompts from llm_prompt table (not task prompts)."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT id, name, description, 
                       COALESCE(system_prompt, '') as system_prompt,
                       COALESCE(prompt_text, '') as prompt_text
                FROM llm_prompt
                WHERE system_prompt IS NOT NULL AND system_prompt != ''
                ORDER BY name
            """)
            prompts = cur.fetchall()
            
        return jsonify([dict(p) for p in prompts])
    except Exception as e:
        logger.error(f"Error getting system prompts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/step-config/<stage>/<substage>/<step>', methods=['GET'])
def get_step_config(stage, substage, step):
    """Get step configuration from workflow_step_entity table."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Convert step name from URL format to database format (e.g., "basic_idea" -> "Basic Idea")
            db_step_name = step.replace('_', ' ').title()
            
            # Get step configuration
            cur.execute("""
                SELECT wse.config, wse.id as step_id, wse.name as step_name
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE %s
                AND wsse.name ILIKE %s
                AND wse.name ILIKE %s
            """, (stage, substage, db_step_name))
            
            result = cur.fetchone()
            if not result:
                # Return default configuration if step not found
                default_config = {
                    'inputs': {
                        'input1': {
                            'type': 'textarea',
                            'label': 'Input 1',
                            'db_field': '',
                            'db_table': 'post_development',
                            'required': False,
                            'placeholder': 'Enter text...'
                        }
                    },
                    'outputs': {},
                    'settings': {
                        'llm': {
                            'user_input_mappings': {},
                            'user_output_mapping': {}
                        }
                    }
                }
                return jsonify(default_config)
            
            config = result['config'] or {}
            
            # Ensure required structure exists
            if 'inputs' not in config:
                config['inputs'] = {}
            if 'outputs' not in config:
                config['outputs'] = {}
            if 'settings' not in config:
                config['settings'] = {}
            if 'llm' not in config['settings']:
                config['settings']['llm'] = {}
            if 'user_input_mappings' not in config['settings']['llm']:
                config['settings']['llm']['user_input_mappings'] = {}
            if 'user_output_mapping' not in config['settings']['llm']:
                config['settings']['llm']['user_output_mapping'] = {}
            
            # Add step metadata
            config['step_id'] = result['step_id']
            config['step_name'] = result['step_name']
            
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting step config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/actions/<int:action_id>/execute', methods=['POST'])
def execute_action(action_id):
    """Execute a task prompt."""
    try:
        data = request.get_json()
        
        # First get the llm_action to find the prompt_template_id
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT id, field_name, prompt_template_id, prompt_template
                FROM llm_action 
                WHERE id = %s
            """, (action_id,))
            action = cur.fetchone()
            
        if not action:
            return jsonify({'error': 'LLM action not found'}), 404
            
        action = dict(action)
        
        # Get task prompt from database using prompt_template_id
        prompt_id = action.get('prompt_template_id')
        if prompt_id:
            with get_db_conn() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute("""
                    SELECT id, name, prompt_text, description, system_prompt
                    FROM llm_prompt 
                    WHERE id = %s
                """, (prompt_id,))
                prompt = cur.fetchone()
        else:
            # Fallback to using prompt_template from llm_action
            prompt = {
                'id': action_id,
                'name': action['field_name'],
                'prompt_text': action['prompt_template'],
                'description': None,
                'system_prompt': None
            }
            
        if not prompt:
            return jsonify({'error': 'Task prompt not found'}), 404
            
        prompt = dict(prompt)
        
        # Get input text
        input_text = data.get('input_text', '')
        if not input_text:
            return jsonify({'error': 'No input text provided'}), 400
        
        # Get LLM configuration from database
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT provider_type, model_name, api_base
                FROM llm_config
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            """)
            config = cur.fetchone()
            if not config:
                # Fallback to default configuration
                config = {
                    'provider_type': 'ollama',
                    'model_name': 'mistral',
                    'api_base': 'http://localhost:11434'
                }
        
        # Process prompt - replace {{input}} placeholder with actual input
        prompt_template = prompt['prompt_text']
        system_prompt = prompt.get('system_prompt')
        
        if '{{input}}' in prompt_template:
            canonical_prompt = prompt_template.replace('{{input}}', input_text)
        else:
            # If no placeholder, append input to the end
            canonical_prompt = prompt_template + "\n\nInput: " + input_text
        
        # Prepend system prompt if it exists
        if system_prompt:
            canonical_prompt = system_prompt + "\n\n" + canonical_prompt
        
        # Call LLM with configuration
        llm_service = LLMService()
        result = llm_service.generate(
            prompt=canonical_prompt,
            model_name=config['model_name'],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Save output to database if post_id and output_field are provided
        post_id = data.get('post_id')
        output_field = data.get('output_field', 'provisional_title')  # Default field
        section_id = data.get('section_id')
        
        if post_id and output_field:
            try:
                # Check if this is a section-specific field
                section_fields = [
                    'image_concepts', 'image_prompts', 'image_meta_descriptions',
                    'image_captions', 'ideas_to_include', 'facts_to_include',
                    'draft', 'polished', 'highlighting', 'watermarking', 'status'
                ]
                
                if output_field in section_fields and section_id:
                    # Save to specific section via sections API
                    sections_api_url = f"http://localhost:5003/api/sections/{section_id}"
                    update_data = {output_field: result}
                    response = requests.put(sections_api_url, json=update_data, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Saved LLM output to {output_field} for section {section_id}")
                    else:
                        logger.error(f"Failed to save to sections API: {response.status_code} - {response.text}")
                else:
                    # Save to post_development table
                    with get_db_conn() as conn:
                        cur = conn.cursor()
                        
                        # Check if record exists
                        cur.execute("""
                            SELECT id FROM post_development 
                            WHERE post_id = %s
                        """, (post_id,))
                        
                        db_result = cur.fetchone()
                        if not db_result:
                            # Create new record
                            cur.execute(f"""
                                INSERT INTO post_development (post_id, {output_field})
                                VALUES (%s, %s)
                            """, (post_id, result))
                        else:
                            # Update existing record
                            cur.execute(f"""
                                UPDATE post_development 
                                SET {output_field} = %s
                                WHERE post_id = %s
                            """, (result, post_id))
                        
                        conn.commit()
                        logger.info(f"Saved LLM output to {output_field} for post {post_id}")
            except Exception as e:
                logger.error(f"Error saving LLM output to database: {str(e)}")
                # Continue even if save fails - still return the result
        
        return jsonify({'output': result})
        
    except Exception as e:
        logger.error(f"Error executing task prompt {action_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/fields/available')
def get_available_fields():
    """Get available fields for current step."""
    try:
        step_id = request.args.get('step_id')
        if not step_id:
            return jsonify({'error': 'step_id parameter required'}), 400
            
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get available fields from post_development table
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'post_development' 
                AND column_name NOT IN ('id', 'post_id', 'created_at', 'updated_at')
                ORDER BY ordinal_position
            """)
            
            fields = []
            for row in cur.fetchall():
                fields.append({
                    'name': row['column_name'],
                    'type': row['data_type'],
                    'display_name': row['column_name'].replace('_', ' ').title()
                })
            
            return jsonify(fields)
            
    except Exception as e:
        logger.exception(f"Error getting available fields: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/available-fields/<stage>', methods=['GET'])
def get_available_fields_by_stage(stage):
    """Get all available database fields organized by workflow field mapping priority."""
    try:
        substage = request.args.get('substage', 'idea')
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Determine which table to use based on stage and substage
            if stage.lower() == 'writing' and substage.lower() == 'post_info':
                # For post_info substage, use both post and post_development tables
                table_names = ['post', 'post_development']
            elif stage.lower() == 'writing':
                table_name = 'post_section'
                table_names = [table_name]
            else:
                table_name = 'post_development'
                table_names = [table_name]
            
            # Get all fields from the relevant tables
            all_field_names = []
            for table_name in table_names:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND column_name NOT IN ('id', 'post_id', 'created_at', 'updated_at')
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = cur.fetchall()
                all_field_names.extend([col[0] for col in columns])
            
            # Get mapped fields for this stage/substage with their order
            cur.execute("""
                SELECT 
                    wfm.field_name,
                    wfm.display_name,
                    wfm.table_name,
                    wfm.order_index,
                    wfm.field_type
                FROM workflow_field_mapping wfm
                LEFT JOIN workflow_stage_entity ws ON wfm.stage_id = ws.id
                LEFT JOIN workflow_sub_stage_entity wss ON wfm.substage_id = wss.id
                WHERE ws.name = %s AND wss.name = %s
                ORDER BY wfm.order_index ASC, wfm.field_name ASC
            """, (stage, substage))
            
            mapped_fields = cur.fetchall()
            mapped_field_names = [field['field_name'] for field in mapped_fields]
            
            # Create field objects, prioritizing mapped fields first
            fields = []
            
            # Add mapped fields first (in their defined order)
            for field in mapped_fields:
                fields.append({
                    'field_name': field['field_name'],
                    'display_name': field['display_name'] or field['field_name'].replace('_', ' ').title(),
                    'db_table': field['table_name'] or table_names[0],
                    'stage': stage,
                    'type': field['field_type'] or 'text',
                    'mapped': True,
                    'order_index': field['order_index'] or 0
                })
            
            # Add remaining unmapped fields (alphabetically)
            unmapped_fields = [name for name in all_field_names if name not in mapped_field_names]
            for field_name in sorted(unmapped_fields):
                # Determine which table this field belongs to
                db_table = table_names[0]  # Default to first table
                for table_name in table_names:
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, (table_name, field_name))
                    if cur.fetchone():
                        db_table = table_name
                        break
                
                fields.append({
                    'field_name': field_name,
                    'display_name': field_name.replace('_', ' ').title(),
                    'db_table': db_table,
                    'stage': stage,
                    'type': 'text',
                    'mapped': False,
                    'order_index': 999  # Put unmapped fields at the end
                })
            
        return jsonify({'fields': fields})
    except Exception as e:
        logger.error(f"Error getting available fields for stage {stage}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/posts/<int:post_id>/development', methods=['GET', 'PATCH'])
def get_post_development(post_id):
    """Get or update current field values from post_development table."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            if request.method == 'GET':
                # Get all field values for the post
                cur.execute("""
                    SELECT * FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cur.fetchone()
                if not result:
                    # Create empty record if none exists
                    return jsonify({})
                
                # Convert to dict, excluding internal fields
                field_values = {}
                for key, value in result.items():
                    if key not in ['id', 'post_id', 'created_at', 'updated_at']:
                        field_values[key] = value
                
                return jsonify(field_values)
                
            elif request.method == 'PATCH':
                # Update specific field values
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Check if record exists
                cur.execute("""
                    SELECT id FROM post_development 
                    WHERE post_id = %s
                """, (post_id,))
                
                result = cur.fetchone()
                if not result:
                    # Create new record
                    fields = list(data.keys())
                    placeholders = ', '.join([f'%s' for _ in fields])
                    field_names = ', '.join(fields)
                    values = [post_id] + list(data.values())
                    
                    cur.execute(f"""
                        INSERT INTO post_development (post_id, {field_names})
                        VALUES ({placeholders})
                    """, values)
                else:
                    # Update existing record
                    set_clauses = []
                    values = []
                    for field, value in data.items():
                        set_clauses.append(f"{field} = %s")
                        values.append(value)
                    
                    values.append(post_id)
                    cur.execute(f"""
                        UPDATE post_development 
                        SET {', '.join(set_clauses)}
                        WHERE post_id = %s
                    """, values)
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Post development updated'})
            
    except Exception as e:
        logger.exception(f"Error with post development: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/posts/<int:post_id>/post', methods=['GET', 'PATCH'])
def get_post_data(post_id):
    """Get or update current field values from post table."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            if request.method == 'GET':
                # Get all field values for the post
                cur.execute("""
                    SELECT * FROM post 
                    WHERE id = %s
                """, (post_id,))
                
                result = cur.fetchone()
                if not result:
                    return jsonify({'error': 'Post not found'}), 404
                
                # Convert to dict, excluding internal fields
                field_values = {}
                for key, value in result.items():
                    if key not in ['id', 'created_at', 'updated_at']:
                        field_values[key] = value
                
                return jsonify(field_values)
                
            elif request.method == 'PATCH':
                # Update specific field values
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Update post record
                set_clauses = []
                values = []
                for field, value in data.items():
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
                
                values.append(post_id)
                cur.execute(f"""
                    UPDATE post 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """, values)
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Post updated'})
            
    except Exception as e:
        logger.exception(f"Error with post data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/field-content')
def get_field_content():
    """Load content for specific field."""
    try:
        post_id = request.args.get('post_id')
        field_name = request.args.get('field_name')
        
        if not post_id or not field_name:
            return jsonify({'error': 'post_id and field_name parameters required'}), 400
            
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get specific field content
            cur.execute(f"""
                SELECT {field_name} FROM post_development 
                WHERE post_id = %s
            """, (post_id,))
            
            result = cur.fetchone()
            if not result:
                return jsonify({'content': ''})
            
            return jsonify({'content': result[field_name]})
            
    except Exception as e:
        logger.exception(f"Error getting field content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/post_section_fields', methods=['GET'])
def get_post_section_fields():
    """Get all available fields from the post_section table for Writing stage."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            # Get column information for post_section table
            cur.execute("""
                SELECT 
                    column_name as field_name,
                    column_name as display_name
                FROM information_schema.columns 
                WHERE table_name = 'post_section' 
                AND column_name NOT IN ('id', 'post_id', 'section_order', 'image_id', 'image_prompt_example_id')
                ORDER BY ordinal_position
            """)
            fields = cur.fetchall()
            
            # Convert to list of dictionaries with better display names
            field_list = []
            for field in fields:
                field_dict = dict(field)
                # Create a better display name
                display_name = field_dict['field_name'].replace('_', ' ').title()
                field_dict['display_name'] = display_name
                field_list.append(field_dict)
            
            return jsonify(field_list)
    except Exception as e:
        logger.error(f"Error getting post section fields: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/field-mappings', methods=['GET', 'POST'])
def field_mappings():
    """Save/load field selections for current step."""
    try:
        if request.method == 'GET':
            # Get context parameters
            stage = request.args.get('stage', 'planning')
            substage = request.args.get('substage', 'idea')
            step = request.args.get('step', 'basic_idea')
            step_id = request.args.get('step_id')
            
            with get_db_conn() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                # Get existing field mappings for this step
                if step_id:
                    cur.execute("""
                        SELECT field_name, mapped_field, section, table_name
                        FROM workflow_field_mappings 
                        WHERE step_id = %s
                    """, (step_id,))
                else:
                    # Get step ID first
                    cur.execute("""
                        SELECT ws.id as step_id
                        FROM workflow_stage_entity s
                        LEFT JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id AND ss.name = %s
                        LEFT JOIN workflow_step_entity ws ON ws.sub_stage_id = ss.id AND ws.name = %s
                        WHERE s.name = %s
                    """, (substage, step, stage))
                    
                    step_result = cur.fetchone()
                    if not step_result:
                        return jsonify([])
                    
                    cur.execute("""
                        SELECT field_name, mapped_field, section, table_name
                        FROM workflow_field_mappings 
                        WHERE step_id = %s
                    """, (step_result['step_id'],))
                
                mappings = [dict(row) for row in cur.fetchall()]
                return jsonify(mappings)
                
        elif request.method == 'POST':
            data = request.get_json()
            step_id = data.get('step_id')
            mappings = data.get('mappings', [])
            
            if not step_id:
                return jsonify({'error': 'step_id required'}), 400
            
            with get_db_conn() as conn:
                cur = conn.cursor()
                
                # Clear existing mappings for this step
                cur.execute("DELETE FROM workflow_field_mappings WHERE step_id = %s", (step_id,))
                
                # Insert new mappings
                for mapping in mappings:
                    # Extract table name from full field ID if present
                    table_name = 'post_development'  # default
                    if 'table_name' in mapping:
                        table_name = mapping['table_name']
                    elif 'mapped_field' in mapping and '.' in mapping['mapped_field']:
                        table_name = mapping['mapped_field'].split('.')[0]
                    
                    cur.execute("""
                        INSERT INTO workflow_field_mappings (step_id, field_name, mapped_field, section, table_name)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (step_id, mapping['field_name'], mapping['mapped_field'], mapping['section'], table_name))
                
                conn.commit()
                return jsonify({'success': True})
                
    except Exception as e:
        logger.exception(f"Error with field mappings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/step/<int:step_id>/field-selection', methods=['POST'])
def save_field_selection(step_id):
    """Save field selection to step configuration."""
    try:
        data = request.get_json()
        input_field = data.get('input_field')
        input_table = data.get('input_table', 'post_development')
        input_id = data.get('input_id')
        
        if not input_field or not input_id:
            return jsonify({'error': 'input_field and input_id required'}), 400
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get current step configuration
            cur.execute("SELECT config FROM workflow_step_entity WHERE id = %s", (step_id,))
            step = cur.fetchone()
            if not step:
                return jsonify({'error': 'Step not found'}), 404
            
            config = step['config'] or {}
            
            # Ensure settings.llm structure exists
            if 'settings' not in config:
                config['settings'] = {}
            if 'llm' not in config['settings']:
                config['settings']['llm'] = {}
            if 'user_input_mappings' not in config['settings']['llm']:
                config['settings']['llm']['user_input_mappings'] = {}
            
            # Update the input mapping
            config['settings']['llm']['user_input_mappings'][input_id] = {
                'field': input_field,
                'table': input_table
            }
            
            # Save updated configuration
            cur.execute("""
                UPDATE workflow_step_entity 
                SET config = %s::jsonb 
                WHERE id = %s
            """, (json.dumps(config), step_id))
            
            conn.commit()
            
        return jsonify({'success': True, 'message': 'Field selection saved'})
        
    except Exception as e:
        logger.error(f"Error saving field selection: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow/step-settings', methods=['GET', 'POST'])
def get_step_settings():
    """Get step settings for a specific post and step."""
    try:
        # Handle POST request for saving settings
        if request.method == 'POST':
            data = request.get_json()
            post_id = data.get('post_id')
            step_id = data.get('step_id')
            task_prompt_id = data.get('task_prompt_id')
            system_prompt_id = data.get('system_prompt_id')
            
            if not post_id or not step_id:
                return jsonify({'error': 'post_id and step_id required'}), 400
            
            with get_db_conn() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                # Insert or update step settings
                cur.execute("""
                    INSERT INTO workflow_step_prompt (step_id, task_prompt_id, system_prompt_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (step_id) 
                    DO UPDATE SET 
                        task_prompt_id = EXCLUDED.task_prompt_id,
                        system_prompt_id = EXCLUDED.system_prompt_id
                """, (step_id, task_prompt_id, system_prompt_id))
                
                conn.commit()
                logger.info(f"Saved step settings for step_id={step_id}")
                return jsonify({'success': True})
        
        # Handle GET request for retrieving settings
        post_id = request.args.get('post_id')
        step_id = request.args.get('step_id')
        step_name = request.args.get('step')  # Get step name as fallback
        
        if not post_id:
            return jsonify({'error': 'post_id required'}), 400
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            step = None
            step_id_int = None
            
            # If step_id is provided, try to use it directly
            if step_id:
                try:
                    step_id_int = int(step_id)
                    cur.execute("""
                        SELECT config FROM workflow_step_entity 
                        WHERE id = %s
                    """, (step_id_int,))
                    step = cur.fetchone()
                except ValueError:
                    step = None
            
            # If step_id didn't work or wasn't provided, try to find by step name
            if not step and step_name:
                # Try exact match first
                cur.execute("""
                    SELECT config FROM workflow_step_entity 
                    WHERE name = %s
                    LIMIT 1
                """, (step_name,))
                step = cur.fetchone()
                
                # If no exact match, try case-insensitive match
                if not step:
                    cur.execute("""
                        SELECT config FROM workflow_step_entity 
                        WHERE LOWER(name) = LOWER(%s)
                        LIMIT 1
                    """, (step_name,))
                    step = cur.fetchone()
            
            # If still no step found, return empty settings
            if not step:
                logger.warning(f"No step found for post_id={post_id}, step_id={step_id}, step_name={step_name}")
                return jsonify({
                    'task_prompt_id': None,
                    'system_prompt_id': None,
                    'task_prompt_text': '',
                    'system_prompt_text': ''
                })
            
            config = step['config'] or {}
            settings = config.get('settings', {})
            llm_settings = settings.get('llm', {})
            
            # Get prompt settings from workflow_step_prompt table
            step_id_for_query = step_id_int
            cur.execute("""
                SELECT task_prompt_id, system_prompt_id 
                FROM workflow_step_prompt 
                WHERE step_id = %s
            """, (step_id_for_query,))
            
            prompt_settings = cur.fetchone()
            
            # Get the actual prompt text from the database
            task_prompt_text = ''
            system_prompt_text = ''
            
            if prompt_settings and prompt_settings['task_prompt_id']:
                cur.execute("SELECT prompt_template FROM llm_action WHERE id = %s", (prompt_settings['task_prompt_id'],))
                task_result = cur.fetchone()
                if task_result:
                    task_prompt_text = task_result['prompt_template'] or ''
            
            if prompt_settings and prompt_settings['system_prompt_id']:
                cur.execute("SELECT prompt_text FROM llm_prompt WHERE id = %s", (prompt_settings['system_prompt_id'],))
                system_result = cur.fetchone()
                if system_result:
                    system_prompt_text = system_result['prompt_text'] or ''
            
            result = {
                'task_prompt_id': prompt_settings['task_prompt_id'] if prompt_settings else None,
                'system_prompt_id': prompt_settings['system_prompt_id'] if prompt_settings else None,
                'task_prompt_text': task_prompt_text,
                'system_prompt_text': system_prompt_text
            }
            
            return jsonify(result)
            
    except Exception as e:
        logger.exception(f"Error getting step settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow/posts/<int:post_id>/sections', methods=['GET'])
def get_post_sections(post_id):
    """Get sections for a specific post."""
    try:
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get all sections for the post
            cur.execute("""
                SELECT id, title, content, section_type, order_index, created_at, updated_at
                FROM post_section 
                WHERE post_id = %s 
                ORDER BY order_index, created_at
            """, (post_id,))
            
            sections = [dict(row) for row in cur.fetchall()]
            
            # Convert to field values format expected by frontend
            field_values = {}
            for section in sections:
                field_name = f"section_{section['id']}"
                field_values[field_name] = {
                    'id': section['id'],
                    'title': section['title'] or '',
                    'content': section['content'] or '',
                    'type': section['section_type'] or 'text',
                    'order': section['order_index'] or 0
                }
            
            logger.info(f"Retrieved {len(field_values)} sections for post {post_id}")
            return jsonify(field_values)
            
    except Exception as e:
        logger.exception(f"Error getting post sections: {str(e)}")
        # Return empty result instead of error to prevent frontend failures
        return jsonify({})

@app.route('/api/workflow/available-tables', methods=['GET'])
def get_available_tables():
    """Get list of available tables with descriptions."""
    try:
        tables = [
            {'name': 'post_development', 'display_name': 'Post Development', 'description': 'Planning and development fields'},
            {'name': 'post', 'display_name': 'Post Info', 'description': 'Basic post information'},
            {'name': 'post_section', 'display_name': 'Post Sections', 'description': 'Section-specific content'}
        ]
        return jsonify(tables)
    except Exception as e:
        logger.exception(f"Error getting available tables: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow/fields/by-table', methods=['GET'])
def get_fields_by_table():
    """Get fields from specific table with table context."""
    try:
        table_name = request.args.get('table')
        if not table_name:
            return jsonify({'error': 'table parameter required'}), 400
        
        # Validate table name
        valid_tables = ['post_development', 'post', 'post_section']
        if table_name not in valid_tables:
            return jsonify({'error': f'Invalid table: {table_name}'}), 400
        
        with get_db_conn() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get fields from specific table
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND column_name NOT IN ('id', 'post_id', 'created_at', 'updated_at')
                ORDER BY ordinal_position
            """, (table_name,))
            
            fields = []
            for row in cur.fetchall():
                fields.append({
                    'field_name': row['column_name'],
                    'display_name': row['column_name'].replace('_', ' ').title(),
                    'table_name': table_name,
                    'full_field_id': f"{table_name}.{row['column_name']}",  # Unique identifier
                    'data_type': row['data_type']
                })
            
            return jsonify(fields)
            
    except Exception as e:
        logger.exception(f"Error getting fields by table: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow/table-preferences', methods=['GET', 'POST'])
def manage_table_preferences():
    """Get/set user's table preferences for current step."""
    try:
        if request.method == 'GET':
            # Get current preferences
            step_id = request.args.get('step_id')
            section = request.args.get('section')  # 'input' or 'output'
            
            if not step_id or not section:
                return jsonify({'error': 'step_id and section parameters required'}), 400
            
            with get_db_conn() as conn:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                cur.execute("""
                    SELECT preferred_table 
                    FROM workflow_table_preferences 
                    WHERE step_id = %s AND section = %s AND user_id = 1
                """, (step_id, section))
                
                result = cur.fetchone()
                if result:
                    return jsonify({'preferred_table': result['preferred_table']})
                else:
                    return jsonify({'preferred_table': None})
                    
        elif request.method == 'POST':
            # Set new preference
            data = request.get_json()
            step_id = data.get('step_id')
            section = data.get('section')
            preferred_table = data.get('preferred_table')
            
            if not all([step_id, section, preferred_table]):
                return jsonify({'error': 'step_id, section, and preferred_table required'}), 400
            
            # Validate table name
            valid_tables = ['post_development', 'post', 'post_section']
            if preferred_table not in valid_tables:
                return jsonify({'error': f'Invalid table: {preferred_table}'}), 400
            
            with get_db_conn() as conn:
                cur = conn.cursor()
                
                # Upsert preference
                cur.execute("""
                    INSERT INTO workflow_table_preferences (step_id, section, preferred_table, user_id)
                    VALUES (%s, %s, %s, 1)
                    ON CONFLICT (step_id, section, user_id) 
                    DO UPDATE SET preferred_table = EXCLUDED.preferred_table, updated_at = CURRENT_TIMESTAMP
                """, (step_id, section, preferred_table))
                
                conn.commit()
                return jsonify({'success': True, 'preferred_table': preferred_table})
                
    except Exception as e:
        logger.exception(f"Error managing table preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Register preview blueprint
app.register_blueprint(preview_bp, url_prefix='/preview')

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'llm-actions'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True) 