"""
Image Generation Services

Core business logic for image generation including DALL-E and SDXL integration.
"""

import os
import requests
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service class for image generation operations"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    def generate_dalle_image(self, image_prompt: str, post_id: int, section_id: int, 
                           model_name: str = 'dall-e-3', parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate image using DALL-E API"""
        try:
            if parameters is None:
                parameters = {}
                
            # Load OpenAI API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {'success': False, 'error': 'OPENAI_API_KEY not found in environment'}
            
            # Call DALL-E API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use parameters or defaults
            size = parameters.get('image-dimensions', '1792x1024')
            quality = parameters.get('quality', 'standard')
            style = parameters.get('style-setting', 'natural')
            
            data = {
                'model': model_name,
                'prompt': image_prompt,
                'n': 1,
                'size': size,
                'quality': quality,
                'style': style
            }
            
            response = requests.post('https://api.openai.com/v1/images/generations', 
                                   headers=headers, json=data, timeout=60)
            
            if response.status_code != 200:
                return {'success': False, 'error': f'DALL-E API error: {response.status_code} - {response.text}'}
            
            result = response.json()
            
            if 'data' not in result or not result['data']:
                return {'success': False, 'error': 'No image data returned from DALL-E'}
            
            # Download the image
            image_url = result['data'][0]['url']
            image_response = requests.get(image_url, timeout=30)
            
            if image_response.status_code != 200:
                return {'success': False, 'error': f'Failed to download image: {image_response.status_code}'}
            
            # Create directory structure
            image_dir = f"{self.project_root}/static/content/posts/{post_id}/sections/{section_id}/raw"
            os.makedirs(image_dir, exist_ok=True)
            
            # Save image with section-based naming
            image_path = f"{image_dir}/{section_id}.png"
            with open(image_path, 'wb') as f:
                f.write(image_response.content)
            
            return {
                'success': True,
                'image_path': f"/static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png",
                'local_path': image_path
            }
            
        except Exception as e:
            logger.error(f"DALL-E generation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_sdxl_image(self, image_prompt: str, post_id: int, section_id: int, 
                          parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate image using SDXL + LoRA"""
        try:
            if parameters is None:
                parameters = {}
                
            # Use parameters or defaults
            dimensions = parameters.get('image-dimensions', '1792x1024')
            style = parameters.get('style-setting', 'watercolor')
            steps = int(parameters.get('steps', 30))
            cfg = float(parameters.get('cfg', 6.5))
            seed = int(parameters.get('seed', 999))
            
            # Call the SDXL script
            cmd = [
                'bash', '-c',
                f'source {self.project_root}/venv_sdxl/bin/activate && python3 {self.project_root}/scripts/generate_sdxl_lora_integrated.py --post_id {post_id} --section_id {section_id} --subject "{image_prompt}" --dimensions "{dimensions}" --steps {steps} --cfg {cfg} --seed {seed}'
            ]
            
            logger.info(f"Running SDXL command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"SDXL script failed: {result.stderr}")
                return {'success': False, 'error': f'SDXL generation failed: {result.stderr}'}
            
            # Check if image was created
            image_path = f"{self.project_root}/static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png"
            if os.path.exists(image_path):
                return {
                    'success': True,
                    'image_path': f"/static/content/posts/{post_id}/sections/{section_id}/raw/{section_id}.png",
                    'local_path': image_path,
                    'message': f'SDXL image generated successfully with {dimensions} dimensions'
                }
            else:
                return {'success': False, 'error': 'Image file not found after generation'}
                
        except subprocess.TimeoutExpired:
            logger.error("SDXL generation timed out")
            return {'success': False, 'error': 'SDXL generation timed out'}
        except Exception as e:
            logger.error(f"SDXL generation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_image(self, image_prompt: str, post_id: int, section_id: int, 
                      model_name: str = 'sdxl-lora', parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate image using the specified model"""
        if model_name == 'sdxl-lora':
            return self.generate_sdxl_image(image_prompt, post_id, section_id, parameters)
        elif model_name in ['dall-e-3', 'dall-e-2']:
            return self.generate_dalle_image(image_prompt, post_id, section_id, model_name, parameters)
        else:
            return {'success': False, 'error': f'Unknown model: {model_name}'}
