# modules/prompt_renderers.py
"""
Model-Aware Prompt Rendering System
Handles conversion of canonical prompts to model-specific formats
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class CanonicalPrompt:
    """Canonical prompt structure that works across all models"""
    
    def __init__(self, data: Dict[str, Any]):
        self.subject = data.get('subject', '')
        self.scene = data.get('scene', '')
        self.style = data.get('style', '')
        self.constraints = data.get('constraints', [])
        self.negatives = data.get('negatives', [])
        self.keywords = data.get('keywords', [])
        self.composition = data.get('composition', '')
        self.mood = data.get('mood', '')
        self.lighting = data.get('lighting', '')
        self.colors = data.get('colors', [])
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'subject': self.subject,
            'scene': self.scene,
            'style': self.style,
            'constraints': self.constraints,
            'negatives': self.negatives,
            'keywords': self.keywords,
            'composition': self.composition,
            'mood': self.mood,
            'lighting': self.lighting,
            'colors': self.colors
        }
    
    @classmethod
    def from_legacy_prompt(cls, prompt_text: str) -> 'CanonicalPrompt':
        """Convert legacy prompt text to canonical structure"""
        if not prompt_text:
            return cls({})
        
        # Try to parse as JSON first
        try:
            data = json.loads(prompt_text)
            if isinstance(data, dict):
                return cls(data)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Parse as plain text
        return cls({
            'subject': prompt_text.strip(),
            'scene': '',
            'style': '',
            'constraints': [],
            'negatives': [],
            'keywords': [],
            'composition': '',
            'mood': '',
            'lighting': '',
            'colors': []
        })

class PromptRenderer:
    """Base class for model-specific prompt renderers"""
    
    def __init__(self, model_key: str, constraints: Dict[str, Any]):
        self.model_key = model_key
        self.constraints = constraints
        self.max_chars = constraints.get('max_prompt_chars', 1000)
    
    def render(self, canonical: CanonicalPrompt) -> str:
        """Render canonical prompt to model-specific format"""
        raise NotImplementedError
    
    def _enforce_length_limit(self, prompt: str) -> str:
        """Enforce character limit for the model"""
        if len(prompt) <= self.max_chars:
            return prompt
        
        # Truncate and add ellipsis
        truncated = prompt[:self.max_chars - 3]
        return truncated + "..."
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return list(set(words))

class SDXLRenderer(PromptRenderer):
    """Renderer for SDXL LoRA model - optimized for short, tag-style prompts"""
    
    def render(self, canonical: CanonicalPrompt) -> str:
        """Render canonical prompt for SDXL"""
        parts = []
        
        # Subject (most important)
        if canonical.subject:
            parts.append(canonical.subject)
        
        # Style
        if canonical.style:
            parts.append(f"in {canonical.style} style")
        
        # Scene/context
        if canonical.scene:
            parts.append(f"scene: {canonical.scene}")
        
        # Composition
        if canonical.composition:
            parts.append(f"composition: {canonical.composition}")
        
        # Mood
        if canonical.mood:
            parts.append(f"mood: {canonical.mood}")
        
        # Lighting
        if canonical.lighting:
            parts.append(f"lighting: {canonical.lighting}")
        
        # Colors
        if canonical.colors:
            color_str = ", ".join(canonical.colors)
            parts.append(f"colors: {color_str}")
        
        # Keywords (as tags)
        if canonical.keywords:
            keyword_str = ", ".join(canonical.keywords)
            parts.append(keyword_str)
        
        # Constraints
        if canonical.constraints:
            constraint_str = ", ".join(canonical.constraints)
            parts.append(constraint_str)
        
        # Join with commas for tag-style format
        prompt = ", ".join(parts)
        
        # Add LoRA-specific enhancements
        if self.model_key == 'sdxl-lora':
            prompt = self._add_lora_enhancements(prompt)
        
        return self._enforce_length_limit(prompt)
    
    def _add_lora_enhancements(self, prompt: str) -> str:
        """Add LoRA-specific enhancements for watercolor style"""
        enhancements = [
            "pen and ink watercolor",
            "artistic illustration",
            "hand-drawn style"
        ]
        
        # Add enhancements if not already present
        for enhancement in enhancements:
            if enhancement.lower() not in prompt.lower():
                prompt += f", {enhancement}"
        
        return prompt
    
    def generate_negative_prompt(self, canonical: CanonicalPrompt) -> str:
        """Generate negative prompt for SDXL"""
        negatives = [
            "blurry", "low quality", "distorted", "deformed",
            "oversaturated", "cartoon", "anime", "3d render",
            "photorealistic", "digital art", "computer generated"
        ]
        
        # Add canonical negatives
        if canonical.negatives:
            negatives.extend(canonical.negatives)
        
        return ", ".join(negatives)

class DALLE3Renderer(PromptRenderer):
    """Renderer for DALL-E 3 - optimized for descriptive, natural language"""
    
    def render(self, canonical: CanonicalPrompt) -> str:
        """Render canonical prompt for DALL-E 3"""
        parts = []
        
        # Start with subject
        if canonical.subject:
            parts.append(canonical.subject)
        else:
            parts.append("an image")
        
        # Add scene context
        if canonical.scene:
            parts.append(f"set in {canonical.scene}")
        
        # Add style
        if canonical.style:
            parts.append(f"rendered in {canonical.style} style")
        
        # Add composition details
        if canonical.composition:
            parts.append(f"with {canonical.composition} composition")
        
        # Add mood and atmosphere
        if canonical.mood:
            parts.append(f"conveying a {canonical.mood} mood")
        
        # Add lighting
        if canonical.lighting:
            parts.append(f"with {canonical.lighting} lighting")
        
        # Add color palette
        if canonical.colors:
            color_str = ", ".join(canonical.colors)
            parts.append(f"featuring {color_str} colors")
        
        # Add keywords as descriptive elements
        if canonical.keywords:
            keyword_str = ", ".join(canonical.keywords)
            parts.append(f"including {keyword_str}")
        
        # Add constraints
        if canonical.constraints:
            constraint_str = ", ".join(canonical.constraints)
            parts.append(f"with {constraint_str}")
        
        # Join with natural language connectors
        prompt = " ".join(parts)
        
        # Clean up grammar
        prompt = self._clean_grammar(prompt)
        
        return self._enforce_length_limit(prompt)
    
    def _clean_grammar(self, prompt: str) -> str:
        """Clean up grammar and flow"""
        # Remove double spaces
        prompt = re.sub(r'\s+', ' ', prompt)
        
        # Fix common grammar issues
        prompt = re.sub(r'\bincluding\s+([^,]+),\s*([^,]+)', r'including \1 and \2', prompt)
        prompt = re.sub(r'\bwith\s+([^,]+),\s*([^,]+)', r'with \1 and \2', prompt)
        
        return prompt.strip()

class DALLE2Renderer(PromptRenderer):
    """Renderer for DALL-E 2 - similar to DALL-E 3 but with stricter limits"""
    
    def render(self, canonical: CanonicalPrompt) -> str:
        """Render canonical prompt for DALL-E 2"""
        # Use DALL-E 3 renderer but with stricter length limits
        dalle3_renderer = DALLE3Renderer(self.model_key, self.constraints)
        prompt = dalle3_renderer.render(canonical)
        
        # DALL-E 2 has stricter limits
        if len(prompt) > 1000:
            # Prioritize subject and style
            parts = []
            if canonical.subject:
                parts.append(canonical.subject)
            if canonical.style:
                parts.append(f"in {canonical.style} style")
            if canonical.scene:
                parts.append(f"set in {canonical.scene}")
            
            prompt = ", ".join(parts)
        
        return self._enforce_length_limit(prompt)

class PromptRendererFactory:
    """Factory for creating model-specific renderers"""
    
    @staticmethod
    def create_renderer(model_key: str, constraints: Dict[str, Any]) -> PromptRenderer:
        """Create appropriate renderer for model"""
        if model_key == 'sdxl-lora':
            return SDXLRenderer(model_key, constraints)
        elif model_key == 'dall-e-3':
            return DALLE3Renderer(model_key, constraints)
        elif model_key == 'dall-e-2':
            return DALLE2Renderer(model_key, constraints)
        else:
            # Default to DALL-E 3 renderer for unknown models
            logger.warning(f"Unknown model {model_key}, using DALL-E 3 renderer")
            return DALLE3Renderer(model_key, constraints)

def render_prompt_for_model(canonical_prompt: CanonicalPrompt, model_key: str, constraints: Dict[str, Any]) -> str:
    """Convenience function to render prompt for specific model"""
    renderer = PromptRendererFactory.create_renderer(model_key, constraints)
    return renderer.render(canonical_prompt)

def parse_legacy_prompt(prompt_text: str) -> CanonicalPrompt:
    """Parse legacy prompt text into canonical structure"""
    return CanonicalPrompt.from_legacy_prompt(prompt_text)
