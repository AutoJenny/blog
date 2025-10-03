"""
Image Generation Module

Handles all image generation functionality including:
- DALL-E API integration
- SDXL + LoRA local generation
- Model parameter management
- API endpoints for image generation
"""

from .services import ImageGenerationService

__all__ = ['ImageGenerationService']
