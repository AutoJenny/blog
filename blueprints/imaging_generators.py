"""
Image Generation Functions
Model-specific image generation implementations (DALL-E, GPT-Image-1, SDXL)
"""

import os
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def imaging_generate_dalle_image(image_prompt, post_id, section_id, parameters):
    """Generate image using DALL-E API - generates both landscape and portrait versions"""
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
        
        # Create directory structure
        if section_id == 'header':
            landscape_dir = f"static/content/posts/{post_id}/header/raw"
            portrait_dir = f"static/content/posts/{post_id}/header/portrait/raw"
            landscape_filename = "header.png"
            portrait_filename = "header_portrait.png"
        else:
            landscape_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            portrait_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
            landscape_filename = f"{section_id}.png"
            portrait_filename = f"{section_id}_portrait.png"
        
        os.makedirs(landscape_dir, exist_ok=True)
        os.makedirs(portrait_dir, exist_ok=True)
        
        landscape_path = f"{landscape_dir}/{landscape_filename}"
        
        # Always generate and overwrite existing image (don't skip if file exists)
        landscape_data = {
            'model': 'dall-e-3',
            'prompt': image_prompt,
            'n': 1,
            'size': landscape_size,
            'quality': quality,
            'style': style
        }
        
        logger.info(f"DALL-E landscape API request: {landscape_data}")
        landscape_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=landscape_data, timeout=120)
        
        if landscape_response.status_code != 200:
            return {'success': False, 'error': f'DALL-E landscape API error: {landscape_response.status_code} - {landscape_response.text}'}
        
        landscape_result = landscape_response.json()
        if 'data' not in landscape_result or not landscape_result['data']:
            return {'success': False, 'error': 'No image data returned from DALL-E landscape'}
        
        # Download landscape image
        landscape_url = landscape_result['data'][0]['url']
        landscape_image_response = requests.get(landscape_url, timeout=30)
        if landscape_image_response.status_code != 200:
            return {'success': False, 'error': f'Failed to download landscape image: {landscape_image_response.status_code}'}
        
        # Always overwrite existing file
        with open(landscape_path, 'wb') as f:
            f.write(landscape_image_response.content)
        logger.info(f"Generated and saved landscape image: {landscape_path} (overwrote existing if present)")
        
        # Generate portrait version with same prompt but portrait dimensions
        portrait_data = {
            'model': 'dall-e-3',
            'prompt': image_prompt,
            'n': 1,
            'size': portrait_size,
            'quality': quality,
            'style': style
        }
        
        logger.info(f"DALL-E portrait API request: {portrait_data}")
        portrait_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=portrait_data, timeout=120)
        
        portrait_success = False
        portrait_path = None
        if portrait_response.status_code == 200:
            portrait_result = portrait_response.json()
            if 'data' in portrait_result and portrait_result['data']:
                # Download portrait image
                portrait_url = portrait_result['data'][0]['url']
                portrait_image_response = requests.get(portrait_url, timeout=30)
                if portrait_image_response.status_code == 200:
                    portrait_path = f"{portrait_dir}/{portrait_filename}"
                    logger.info(f"Saving portrait image to: {portrait_path} (size: {len(portrait_image_response.content)} bytes)")
                    try:
                        with open(portrait_path, 'wb') as f:
                            f.write(portrait_image_response.content)
                        portrait_success = True
                        logger.info(f"Portrait image saved successfully to: {portrait_path}")
                    except Exception as e:
                        logger.error(f"Failed to save portrait image to {portrait_path}: {e}")
                        portrait_success = False
                    logger.info(f"Successfully generated portrait: {portrait_path}")
                else:
                    error_msg = f"Failed to download portrait image: {portrait_image_response.status_code}"
                    logger.warning(error_msg)
                    print(f"ERROR: {error_msg}")  # Also print for script visibility
            else:
                error_msg = "No image data returned from DALL-E portrait"
                logger.warning(error_msg)
                print(f"ERROR: {error_msg}")
        else:
            error_msg = f"DALL-E portrait API error: {portrait_response.status_code} - {portrait_response.text}"
            logger.warning(error_msg)
            print(f"ERROR: {error_msg}")  # Print for visibility when called from script
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{landscape_filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{landscape_filename}",
            'local_path': landscape_path,
            'portrait_generated': portrait_success,
            'portrait_path': f"/static/content/posts/{post_id}/header/portrait/raw/{portrait_filename}" if section_id == 'header' and portrait_success else (f"/static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{portrait_filename}" if portrait_success else None)
        }
        
    except Exception as e:
        logger.error(f"DALL-E generation error: {str(e)}")
        return {'success': False, 'error': str(e)}


def imaging_generate_gpt_image_1(image_prompt, post_id, section_id, parameters):
    """Generate image using GPT-Image-1 API - generates both landscape and portrait versions"""
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
        landscape_size = parameters.get('size', '1536x1024')  # Default landscape for GPT-Image-1
        quality = parameters.get('quality', 'hd')
        style = parameters.get('style', 'natural')
        portrait_size = parameters.get('portrait_size', '1024x1792')  # Default portrait
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Create directory structure
        if section_id == 'header':
            landscape_dir = f"static/content/posts/{post_id}/header/raw"
            portrait_dir = f"static/content/posts/{post_id}/header/portrait/raw"
            landscape_filename = "header.png"
            portrait_filename = "header_portrait.png"
        else:
            landscape_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            portrait_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
            landscape_filename = f"{section_id}.png"
            portrait_filename = f"{section_id}_portrait.png"
        
        os.makedirs(landscape_dir, exist_ok=True)
        os.makedirs(portrait_dir, exist_ok=True)
        
        landscape_path = f"{landscape_dir}/{landscape_filename}"
        
        # GPT-Image-1 API endpoint
        landscape_data = {
            'model': 'gpt-image-1',
            'prompt': image_prompt,
            'n': 1,
            'size': landscape_size,
            'quality': quality,
            'style': style
        }
        
        logger.info(f"GPT-Image-1 landscape API request: {landscape_data}")
        landscape_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=landscape_data, timeout=120)
        
        if landscape_response.status_code != 200:
            return {'success': False, 'error': f'GPT-Image-1 landscape API error: {landscape_response.status_code} - {landscape_response.text}'}
        
        landscape_result = landscape_response.json()
        if 'data' not in landscape_result or not landscape_result['data']:
            return {'success': False, 'error': 'No image data returned from GPT-Image-1 landscape'}
        
        # Download landscape image
        landscape_url = landscape_result['data'][0]['url']
        landscape_image_response = requests.get(landscape_url, timeout=30)
        if landscape_image_response.status_code != 200:
            return {'success': False, 'error': f'Failed to download landscape image: {landscape_image_response.status_code}'}
        
        # Always overwrite existing file
        with open(landscape_path, 'wb') as f:
            f.write(landscape_image_response.content)
        logger.info(f"Generated and saved landscape image: {landscape_path} (overwrote existing if present)")
        
        # Generate portrait version
        portrait_data = {
            'model': 'gpt-image-1',
            'prompt': image_prompt,
            'n': 1,
            'size': portrait_size,
            'quality': quality,
            'style': style
        }
        
        logger.info(f"GPT-Image-1 portrait API request: {portrait_data}")
        portrait_response = requests.post('https://api.openai.com/v1/images/generations', 
                               headers=headers, json=portrait_data, timeout=120)
        
        portrait_success = False
        portrait_path = None
        if portrait_response.status_code == 200:
            portrait_result = portrait_response.json()
            if 'data' in portrait_result and portrait_result['data']:
                portrait_url = portrait_result['data'][0]['url']
                portrait_image_response = requests.get(portrait_url, timeout=30)
                if portrait_image_response.status_code == 200:
                    portrait_path = f"{portrait_dir}/{portrait_filename}"
                    with open(portrait_path, 'wb') as f:
                        f.write(portrait_image_response.content)
                    portrait_success = True
                    logger.info(f"Successfully generated portrait: {portrait_path}")
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{landscape_filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{landscape_filename}",
            'local_path': landscape_path,
            'portrait_generated': portrait_success,
            'portrait_path': f"/static/content/posts/{post_id}/header/portrait/raw/{portrait_filename}" if section_id == 'header' and portrait_success else (f"/static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{portrait_filename}" if portrait_success else None)
        }
        
    except Exception as e:
        logger.error(f"GPT-Image-1 generation error: {str(e)}")
        return {'success': False, 'error': str(e)}


def imaging_generate_sdxl_image(image_prompt, post_id, section_id, parameters):
    """Generate image using SDXL - generates both landscape and portrait versions"""
    try:
        # Extract parameters
        landscape_width = parameters.get('width', 1024)
        landscape_height = parameters.get('height', 1024)
        portrait_width = parameters.get('portrait_width', 1024)
        portrait_height = parameters.get('portrait_height', 1792)
        steps = parameters.get('steps', 20)
        cfg = parameters.get('cfg', 7.5)
        lora_scale = parameters.get('lora_scale', 0.85)
        seed = parameters.get('seed', None)
        
        # Call SDXL script
        import subprocess
        
        # Use the virtual environment
        venv_python = os.path.join(os.getcwd(), 'venv_sdxl', 'bin', 'python')
        if not os.path.exists(venv_python):
            return {'success': False, 'error': 'SDXL virtual environment not found. Please run setup_sdxl.sh first.'}
        
        # Create directory structure
        if section_id == 'header':
            landscape_dir = f"static/content/posts/{post_id}/header/raw"
            portrait_dir = f"static/content/posts/{post_id}/header/portrait/raw"
            landscape_filename = "header.png"
            portrait_filename = "header_portrait.png"
        else:
            landscape_dir = f"static/content/posts/{post_id}/sections/{section_id}/raw"
            portrait_dir = f"static/content/posts/{post_id}/sections/{section_id}/portrait/raw"
            landscape_filename = f"{section_id}.png"
            portrait_filename = f"{section_id}_portrait.png"
        
        os.makedirs(landscape_dir, exist_ok=True)
        os.makedirs(portrait_dir, exist_ok=True)
        
        # Generate landscape version
        landscape_cmd = [
            venv_python, 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', str(section_id),
            '--width', str(landscape_width),
            '--height', str(landscape_height),
            '--steps', str(steps),
            '--cfg', str(cfg),
            '--lora_scale', str(lora_scale)
        ]
        
        if seed:
            landscape_cmd.extend(['--seed', str(seed)])
        
        landscape_result = subprocess.run(landscape_cmd, capture_output=True, text=True, timeout=300)
        
        if landscape_result.returncode != 0:
            return {'success': False, 'error': f'SDXL landscape generation failed: {landscape_result.stderr}'}
        
        landscape_path = os.path.join(landscape_dir, landscape_filename)
        if not os.path.exists(landscape_path):
            return {'success': False, 'error': 'SDXL landscape generated but image file not found'}
        
        # Generate portrait version
        portrait_cmd = [
            venv_python, 'scripts/generate_sdxl_lora_integrated.py',
            '--subject', image_prompt,
            '--post_id', str(post_id),
            '--section_id', f"{section_id}_portrait",
            '--width', str(portrait_width),
            '--height', str(portrait_height),
            '--steps', str(steps),
            '--cfg', str(cfg),
            '--lora_scale', str(lora_scale)
        ]
        
        if seed:
            portrait_cmd.extend(['--seed', str(seed)])
        
        portrait_result = subprocess.run(portrait_cmd, capture_output=True, text=True, timeout=300)
        
        portrait_success = False
        portrait_path = None
        if portrait_result.returncode == 0:
            # Check if the script created the portrait file (it might use a different naming)
            portrait_temp_path = os.path.join(portrait_dir, portrait_filename)
            # Try to find the generated file
            portrait_candidate = f"static/content/posts/{post_id}/sections/{section_id}_portrait/raw/{section_id}_portrait.png"
            if os.path.exists(portrait_candidate):
                # Move/copy to the correct location
                os.makedirs(portrait_dir, exist_ok=True)
                import shutil
                shutil.move(portrait_candidate, portrait_temp_path)
                portrait_path = portrait_temp_path
                portrait_success = True
            elif os.path.exists(portrait_temp_path):
                portrait_path = portrait_temp_path
                portrait_success = True
        
        return {
            'success': True,
            'image_path': f"/static/content/posts/{post_id}/header/raw/{landscape_filename}" if section_id == 'header' else f"/static/content/posts/{post_id}/sections/{section_id}/raw/{landscape_filename}",
            'local_path': landscape_path,
            'portrait_generated': portrait_success,
            'portrait_path': f"/static/content/posts/{post_id}/header/portrait/raw/{portrait_filename}" if section_id == 'header' and portrait_success else (f"/static/content/posts/{post_id}/sections/{section_id}/portrait/raw/{portrait_filename}" if portrait_success else None)
        }
        
    except Exception as e:
        logger.error(f"SDXL generation error: {str(e)}")
        return {'success': False, 'error': str(e)}

