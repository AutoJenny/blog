"""
Image Generation Functions
Model-specific image generation implementations (DALL-E, GPT-Image-1, SDXL)
"""

import os
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def imaging_generate_dalle_image(image_prompt, post_id, section_id, parameters, orientation='landscape'):
    """Generate image using DALL-E API - generates one image (landscape or portrait)"""
    try:
        # RELOAD .env file directly before checking - ensure we get the latest values
        env_absolute = '/Users/autojenny/Documents/projects/blog/.env'
        
        # Try multiple methods to read the key
        api_key = None
        
        # Method 1: Read directly from file (parse manually)
        try:
            if os.path.exists(env_absolute):
                with open(env_absolute, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'OPENAI_API_KEY':
                                api_key = value.strip()
                                logger.info(f"Found OPENAI_API_KEY in .env file (length: {len(api_key)})")
                                break
        except Exception as e:
            logger.warning(f"Could not read .env file directly: {e}")
        
        # Method 2: Use dotenv_values
        if not api_key:
            try:
                from dotenv import dotenv_values
                env_values = dotenv_values(env_absolute)
                api_key = env_values.get('OPENAI_API_KEY', '')
                if api_key:
                    logger.info(f"Found OPENAI_API_KEY via dotenv_values (length: {len(api_key)})")
            except Exception as e:
                logger.warning(f"Could not read .env via dotenv_values: {e}")
        
        # Method 3: Use load_dotenv and os.getenv
        if not api_key:
            if os.path.exists(env_absolute):
                load_dotenv(dotenv_path=env_absolute, override=True)
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                logger.info(f"Found OPENAI_API_KEY via os.getenv (length: {len(api_key)})")
        
        if not api_key:
            # Try to get from config system as fallback
            try:
                from config.unified_config import get_openai_api_key
                api_key = get_openai_api_key()
            except Exception:
                pass
        
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not found in environment. Please set it in your .env file.'}
        
        # Validate API key format (should start with sk-)
        if not api_key.startswith('sk-'):
            return {'success': False, 'error': 'Invalid OPENAI_API_KEY format. API keys should start with "sk-".'}
        
        # Extract parameters
        landscape_size = parameters.get('size', '1792x1024')  # Default landscape
        quality = parameters.get('quality', 'hd')  # DALL-E 3: 'standard' or 'hd'
        style = parameters.get('style', 'natural')
        portrait_size = parameters.get('portrait_size', '1024x1792')  # Default portrait
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Create directory structure based on orientation
        if orientation == 'portrait':
            if section_id == 'header':
                image_dir = f"static/content/posts/{post_id}/header/portrait/raw"
                filename = "header_portrait.png"
            else:
                image_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
                filename = f"{section_id}_portrait.png"
            image_size = parameters.get('portrait_size', portrait_size)
        else:  # landscape
            if section_id == 'header':
                image_dir = f"static/content/posts/{post_id}/header/landscape/raw"
                filename = "header.png"
            else:
                image_dir = f"static/content/posts/{post_id}/sections/{section_id}/landscape/raw"
                filename = f"{section_id}.png"
            image_size = parameters.get('size', landscape_size)
        
        os.makedirs(image_dir, exist_ok=True)
        image_path = f"{image_dir}/{filename}"
        
        # Generate image
        api_data = {
            'model': 'dall-e-3',
            'prompt': image_prompt,
            'n': 1,
            'size': image_size,
            'quality': quality,
            'style': style
        }
        
        logger.info(f"DALL-E {orientation} API request: {api_data}")
        response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=api_data, timeout=120)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'DALL-E {orientation} API error: {response.status_code} - {response.text}'}
        
        result = response.json()
        if 'data' not in result or not result['data']:
            return {'success': False, 'error': f'No image data returned from DALL-E {orientation}'}
        
        # Download image
        image_url = result['data'][0]['url']
        image_response = requests.get(image_url, timeout=30)
        if image_response.status_code != 200:
            return {'success': False, 'error': f'Failed to download {orientation} image: {image_response.status_code}'}
        
        # Save image
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        logger.info(f"Generated and saved {orientation} image: {image_path}")
        
        # Return path
        if section_id == 'header':
            web_path = f"/static/content/posts/{post_id}/header/{orientation}/raw/{filename}"
        else:
            web_path = f"/static/content/posts/{post_id}/sections/{section_id}/{orientation}/raw/{filename}"
        
        return {
            'success': True,
            'image_path': web_path,
            'local_path': image_path
        }
        
    except Exception as e:
        logger.error(f"DALL-E generation error: {str(e)}")
        return {'success': False, 'error': str(e)}


def imaging_generate_gpt_image_1(image_prompt, post_id, section_id, parameters, orientation='landscape'):
    """Generate image using GPT-Image-1 API - generates one image (landscape or portrait)"""
    try:
        # RELOAD .env file directly before checking - ensure we get the latest values
        env_absolute = '/Users/autojenny/Documents/projects/blog/.env'
        
        # Try multiple methods to read the key
        api_key = None
        
        # Method 1: Read directly from file (parse manually)
        try:
            if os.path.exists(env_absolute):
                with open(env_absolute, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'OPENAI_API_KEY':
                                api_key = value.strip()
                                logger.info(f"Found OPENAI_API_KEY in .env file (length: {len(api_key)})")
                                break
        except Exception as e:
            logger.warning(f"Could not read .env file directly: {e}")
        
        # Method 2: Use dotenv_values
        if not api_key:
            try:
                from dotenv import dotenv_values
                env_values = dotenv_values(env_absolute)
                api_key = env_values.get('OPENAI_API_KEY', '')
                if api_key:
                    logger.info(f"Found OPENAI_API_KEY via dotenv_values (length: {len(api_key)})")
            except Exception as e:
                logger.warning(f"Could not read .env via dotenv_values: {e}")
        
        # Method 3: Use load_dotenv and os.getenv
        if not api_key:
            if os.path.exists(env_absolute):
                load_dotenv(dotenv_path=env_absolute, override=True)
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                logger.info(f"Found OPENAI_API_KEY via os.getenv (length: {len(api_key)})")
        
        if not api_key:
            # Try to get from config system as fallback
            try:
                from config.unified_config import get_openai_api_key
                api_key = get_openai_api_key()
            except Exception:
                pass
        
        if not api_key:
            return {'success': False, 'error': 'OPENAI_API_KEY not found in environment. Please set it in your .env file.'}
        
        # Validate API key format (should start with sk-)
        if not api_key.startswith('sk-'):
            return {'success': False, 'error': 'Invalid OPENAI_API_KEY format. API keys should start with "sk-".'}
        
        # Extract parameters
        quality = parameters.get('quality', 'high')
        portrait_size = parameters.get('portrait_size', '1024x1536')  # Default portrait for GPT-Image-1
        landscape_size = parameters.get('size', '1536x1024')  # Default landscape for GPT-Image-1
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Create directory structure based on orientation
        if orientation == 'portrait':
            if section_id == 'header':
                image_dir = f"static/content/posts/{post_id}/header/portrait/raw"
                filename = "header_portrait.png"
            else:
                image_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
                filename = f"{section_id}_portrait.png"
            image_size = parameters.get('portrait_size', portrait_size)
        else:  # landscape
            if section_id == 'header':
                image_dir = f"static/content/posts/{post_id}/header/landscape/raw"
                filename = "header.png"
            else:
                image_dir = f"static/content/posts/{post_id}/sections/{section_id}/landscape/raw"
                filename = f"{section_id}.png"
            image_size = parameters.get('size', landscape_size)
        
        os.makedirs(image_dir, exist_ok=True)
        image_path = f"{image_dir}/{filename}"
        
        # GPT-Image-1 API endpoint
        # NOTE: GPT-Image-1 does NOT support 'style' or 'response_format' parameters (only DALL-E does)
        api_data = {
            'model': 'gpt-image-1',
            'prompt': image_prompt,
            'n': 1,
            'size': image_size,
            'quality': quality
        }
        
        logger.info(f"GPT-Image-1 {orientation} API request: {api_data}")
        response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=api_data, timeout=120)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'GPT-Image-1 {orientation} API error: {response.status_code} - {response.text}'}
        
        result = response.json()
        if 'data' not in result or not result['data']:
            return {'success': False, 'error': f'No image data returned from GPT-Image-1 {orientation}'}
        
        # Check response structure - GPT-Image-1 may return b64_json or url
        first_item = result['data'][0]
        if 'b64_json' in first_item:
            # Decode base64 and save directly
            import base64
            try:
                image_data = base64.b64decode(first_item['b64_json'])
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                logger.info(f"Generated and saved {orientation} image from b64_json: {image_path}")
            except Exception as e:
                return {'success': False, 'error': f'Failed to decode b64_json image: {str(e)}'}
        elif 'url' in first_item:
            # Download image from URL
            image_url = first_item['url']
            image_response = requests.get(image_url, timeout=30)
            if image_response.status_code != 200:
                return {'success': False, 'error': f'Failed to download {orientation} image: {image_response.status_code}'}
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            logger.info(f"Generated and saved {orientation} image from URL: {image_path}")
        else:
            return {'success': False, 'error': f"GPT-Image-1 response missing both 'url' and 'b64_json' keys. Response: {result}"}
        
        # Return path
        if section_id == 'header':
            web_path = f"/static/content/posts/{post_id}/header/{orientation}/raw/{filename}"
        else:
            web_path = f"/static/content/posts/{post_id}/sections/{section_id}/{orientation}/raw/{filename}"
        
        return {
            'success': True,
            'image_path': web_path,
            'local_path': image_path
        }
        
    except Exception as e:
        logger.error(f"GPT-Image-1 generation error: {str(e)}")
        return {'success': False, 'error': str(e)}


def imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters, orientation='landscape'):
    """Generate image using SDXL - generates one image (landscape or portrait)"""
    try:
        # Extract parameters
        steps = parameters.get('steps', 20)
        cfg = parameters.get('cfg', 7.5)
        lora_scale = parameters.get('lora_scale', 0.85)
        seed = parameters.get('seed', None)
        
        # Get dimensions based on orientation
        if orientation == 'portrait':
            image_width = parameters.get('portrait_width', 1024)
            image_height = parameters.get('portrait_height', 1792)
        else:  # landscape
            image_width = parameters.get('width', 1792)
            image_height = parameters.get('height', 1024)
        
        # Call SDXL script
        import subprocess
        
        # Use the virtual environment
        venv_python = os.path.join(os.getcwd(), 'venv_sdxl', 'bin', 'python')
        if not os.path.exists(venv_python):
            return {'success': False, 'error': 'SDXL virtual environment not found. Please run setup_sdxl.sh first.'}
        
        # Create directory structure based on orientation
        if orientation == 'portrait':
            if section_id == 'header':
                image_dir = f"static/content/posts/{post_id}/header/portrait/raw"
                filename = "header_portrait.png"
            else:
                image_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
                filename = f"{section_id}_portrait.png"
        else:  # landscape
            if section_id == 'header':
                image_dir = f"static/content/posts/{post_id}/header/landscape/raw"
                filename = "header.png"
            else:
                image_dir = f"static/content/posts/{post_id}/sections/{section_id}/landscape/raw"
                filename = f"{section_id}.png"
        
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, filename)
        
        # Generate image
        cmd = [
            venv_python, 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', str(section_id),
            '--width', str(image_width),
            '--height', str(image_height),
            '--steps', str(steps),
            '--cfg', str(cfg),
            '--lora_scale', str(lora_scale)
        ]
        
        if seed:
            cmd.extend(['--seed', str(seed)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {'success': False, 'error': f'SDXL {orientation} generation failed: {result.stderr}'}
        
        # Check if file was created (SDXL script might save to a different location)
        if not os.path.exists(image_path):
            # Try alternative location
            alt_path = f"static/content/posts/{post_id}/sections/{section_id}/raw/{filename}"
            if os.path.exists(alt_path):
                import shutil
                shutil.move(alt_path, image_path)
            else:
                return {'success': False, 'error': f'SDXL {orientation} generated but image file not found'}
        
        # Return path
        if section_id == 'header':
            web_path = f"/static/content/posts/{post_id}/header/{orientation}/raw/{filename}"
        else:
            web_path = f"/static/content/posts/{post_id}/sections/{section_id}/{orientation}/raw/{filename}"
        
        return {
            'success': True,
            'image_path': web_path,
            'local_path': image_path
        }
        
    except Exception as e:
        logger.error(f"SDXL generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

