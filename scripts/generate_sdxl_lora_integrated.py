#!/usr/bin/env python3
"""
SDXL + LoRA integration for blog image generation
Integrates with the existing blog system for consistent image generation
"""

import argparse
import os
import sys
import torch
import datetime
import json
from pathlib import Path
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager

# ====== CONFIG ======
SDXL_BASE = "stabilityai/stable-diffusion-xl-base-1.0"  # HuggingFace model ID
LORA_PATH = str(project_root / "static" / "models" / "lora" / "Aether_Watercolor_and_Ink_v1_SDXL_LoRA.safetensors")
OUTPUT_BASE_DIR = str(project_root / "static" / "content" / "posts")

# Style configuration matching your blog's aesthetic
STYLE_SENTENCE = (
    "loose pen-and-ink linework with watercolor washes, subdued earthy ochres, muted greens, soft blue tones, "
    "semi-transparent pigments, edges fading into white paper, visible paper texture, gentle warm golden glow, "
    "spiritual and ancient tone"
)

NEGATIVE = (
    "photorealism, oversaturated colors, neon, glossy digital look, hard poster edges, pure black heavy outlines, "
    "edge-to-edge coverage, flat fills, high contrast, comic cel shading"
)

def pick_device_dtype():
    """Select the best available device and dtype"""
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if torch.backends.mps.is_available():
        # Apple Silicon
        return "mps", torch.float16
    return "cpu", torch.float32

def generate_image_for_section(post_id, section_id, subject_prompt, **kwargs):
    """
    Generate an image for a specific blog section using SDXL + LoRA
    
    Args:
        post_id (int): Blog post ID
        section_id (int): Section ID
        subject_prompt (str): The main subject/content prompt
        **kwargs: Additional generation parameters
    
    Returns:
        dict: Result with success status and image path or error message
    """
    try:
        # Set up output directory
        output_dir = Path(OUTPUT_BASE_DIR) / str(post_id) / "sections" / str(section_id) / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default parameters
        params = {
            'width': kwargs.get('width', 1792),
            'height': kwargs.get('height', 1024),
            'steps': kwargs.get('steps', 30),
            'cfg': kwargs.get('cfg', 5.5),
            'seed': kwargs.get('seed', 42),
            'lora_scale': kwargs.get('lora_scale', 0.85)
        }
        
        # Check if LoRA file exists
        if not os.path.exists(LORA_PATH):
            return {
                'success': False,
                'error': f'LoRA file not found at {LORA_PATH}. Please download and place the LoRA file.'
            }
        
        # Initialize device and pipeline
        device, dtype = pick_device_dtype()
        
        print(f"Loading SDXL pipeline on {device} with {dtype}...")
        pipe = StableDiffusionXLPipeline.from_pretrained(
            SDXL_BASE, 
            torch_dtype=dtype, 
            use_safetensors=True
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(device)
        
        # Load LoRA
        print(f"Loading LoRA from {LORA_PATH}...")
        pipe.load_lora_weights(LORA_PATH)
        
        # Set up generator with seed
        generator = torch.Generator(device=device)
        generator = generator.manual_seed(params['seed'])
        
        # Construct full prompt
        # Check if user already provided detailed styling to avoid duplication
        if any(style_word in subject_prompt.lower() for style_word in ['watercolor', 'pen-and-ink', 'ochres', 'semi-transparent', 'brushstrokes']):
            # User provided detailed styling, use minimal addition
            full_prompt = f"{subject_prompt}, mystical, spiritual, ancient"
        else:
            # Add full style sentence for basic prompts
            prompt = f"{subject_prompt}, mystical, spiritual, ancient"
            full_prompt = f"{prompt}, {STYLE_SENTENCE}"
        
        print(f"Generating image with prompt: {full_prompt}")
        print(f"Parameters: {params}")
        
        # Generate image
        images = pipe(
            prompt=full_prompt,
            negative_prompt=NEGATIVE,
            num_inference_steps=params['steps'],
            guidance_scale=params['cfg'],
            width=params['width'],
            height=params['height'],
            generator=generator,
            cross_attention_kwargs={"scale": params['lora_scale']},
        ).images
        
        # Save image
        output_filename = f"{section_id}.png"
        output_path = output_dir / output_filename
        images[0].save(output_path)
        
        # Return success with relative path for web access
        relative_path = f"/static/content/posts/{post_id}/sections/{section_id}/raw/{output_filename}"
        
        print(f"Image saved: {output_path}")
        
        return {
            'success': True,
            'image_path': relative_path,
            'message': 'Image generated successfully with SDXL + LoRA',
            'parameters': params,
            'prompt': full_prompt
        }
        
    except Exception as e:
        error_msg = f"Error generating image: {str(e)}"
        print(error_msg)
        return {
            'success': False,
            'error': error_msg
        }

def main():
    """Command line interface for testing"""
    parser = argparse.ArgumentParser(description="SDXL + LoRA image generation for blog")
    parser.add_argument("--post_id", type=int, required=True, help="Blog post ID")
    parser.add_argument("--section_id", type=int, required=True, help="Section ID")
    parser.add_argument("--subject", required=True, help="Subject/content prompt")
    parser.add_argument("--dimensions", default="1792x1024", help="Image dimensions (e.g., 1792x1024)")
    parser.add_argument("--width", type=int, default=1792)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=5.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lora_scale", type=float, default=0.85)
    args = parser.parse_args()
    
    # Parse dimensions if provided
    if args.dimensions:
        width, height = map(int, args.dimensions.split('x'))
    else:
        width, height = args.width, args.height
    
    result = generate_image_for_section(
        args.post_id,
        args.section_id,
        args.subject,
        width=width,
        height=height,
        steps=args.steps,
        cfg=args.cfg,
        seed=args.seed,
        lora_scale=args.lora_scale
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
