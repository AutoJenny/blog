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
        """Return prompt as-is without length limits"""
        return prompt
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return list(set(words))

class SDXLRenderer(PromptRenderer):
    """Renderer for SDXL LoRA model - optimized for short, tag-style prompts with progressive compression"""
    
    def __init__(self, model_key, constraints):
        super().__init__(model_key, constraints)
        self.compression_rules = self._load_compression_rules()
    
    def render(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Render canonical prompt for SDXL - return full prompt without truncation"""
        return self._build_full_prompt(canonical, style_json)
    
    def _load_compression_rules(self) -> dict:
        """Load compression rules from database"""
        try:
            from config.database import db_manager
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT rule_type, rule_key, rule_value, priority
                    FROM prompt_compression_rules 
                    WHERE model_key = %s
                    ORDER BY priority ASC
                """, (self.model_key,))
                
                rules = {}
                for row in cursor.fetchall():
                    rule_type = row['rule_type']
                    if rule_type not in rules:
                        rules[rule_type] = {}
                    rules[rule_type][row['rule_key']] = row['rule_value']
                
                return rules
        except Exception as e:
            logger.error(f"Error loading compression rules: {e}")
            return {}
    
    def _build_full_prompt(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Build full prompt with all available details"""
        parts = []
        
        # Subject (most important)
        if canonical.subject:
            parts.append(canonical.subject)
        
        # Style from both canonical and style_json
        style_description = self._translate_style_to_sdxl(canonical, style_json)
        if style_description:
            parts.extend(style_description)
        
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
        
        # Add more detail if we have room (SDXL can handle more than we're giving it)
        if len(prompt) < 350:  # If we have room, add more descriptive elements
            prompt = self._add_sdxl_details(prompt, canonical, style_json)
        
        return prompt
    
    def _translate_style_to_sdxl(self, canonical: CanonicalPrompt, style_json: dict = None) -> list:
        """Translate style JSON to SDXL tags"""
        tags = []
        
        # Start with canonical style
        if canonical.style:
            tags.append(f"in {canonical.style} style")
        
        # Add style_json details if available
        if isinstance(style_json, dict):
            # Essential: palette
            palette = style_json.get('palette')
            if palette and isinstance(palette, list):
                palette_str = ", ".join(palette)
                tags.append(f"colors: {palette_str}")
            
            # Important: brushwork/technique
            brushwork = style_json.get('brushwork')
            if brushwork:
                tags.append(f"brushwork: {brushwork}")
            
            technique = style_json.get('technique')
            if technique and technique != style_json.get('medium'):
                tags.append(f"technique: {technique}")
            
            # Nice-to-have: margins (drop first in compression)
            margins = style_json.get('margins')
            if margins:
                tags.append(f"margins: {margins}")
        
        return tags
    
    def _add_sdxl_details(self, prompt: str, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Add more descriptive details for SDXL if we have room"""
        details = []
        
        # Add texture details based on medium
        if isinstance(style_json, dict):
            medium = style_json.get('medium', '')
            if medium == 'watercolor':
                details.append('soft texture')
            elif medium == 'oil':
                details.append('rich texture')
            elif medium == 'ink':
                details.append('precise lines')
        
        # Add atmospheric details
        if canonical.mood:
            mood_details = {
                'serene': 'calm atmosphere',
                'peaceful': 'tranquil mood',
                'dramatic': 'dramatic atmosphere',
                'mysterious': 'mysterious mood',
                'nostalgic': 'nostalgic feeling',
                'energetic': 'dynamic energy',
                'melancholic': 'melancholic tone'
            }
            mood_detail = mood_details.get(canonical.mood.lower())
            if mood_detail:
                details.append(mood_detail)
        
        # Add lighting details
        if canonical.lighting:
            lighting_details = {
                'golden hour': 'warm light',
                'sunset': 'orange glow',
                'sunrise': 'soft light',
                'moonlight': 'silver light',
                'daylight': 'bright light',
                'dramatic': 'strong contrast',
                'soft': 'gentle light'
            }
            lighting_detail = lighting_details.get(canonical.lighting.lower())
            if lighting_detail:
                details.append(lighting_detail)
        
        # Add composition details
        if canonical.composition:
            comp_details = {
                'rule of thirds': 'balanced composition',
                'centered': 'symmetrical',
                'diagonal': 'dynamic lines',
                'leading lines': 'guided view',
                'framing': 'natural frame'
            }
            comp_detail = comp_details.get(canonical.composition.lower())
            if comp_detail:
                details.append(comp_detail)
        
        # Add scene-specific details
        if canonical.scene:
            scene_details = {
                'mountain': 'rugged terrain',
                'forest': 'towering trees',
                'lake': 'reflections',
                'ocean': 'endless horizon',
                'city': 'urban details',
                'garden': 'lush vegetation'
            }
            for scene_type, scene_detail in scene_details.items():
                if scene_type in canonical.scene.lower():
                    details.append(scene_detail)
                    break
        
        # Add quality descriptors
        quality_descriptors = ['high quality', 'detailed', 'artistic', 'professional']
        for descriptor in quality_descriptors:
            if len(prompt + ', ' + descriptor) < 400:
                details.append(descriptor)
            else:
                break
        
        # Add details to prompt
        if details:
            detail_str = ', '.join(details)
            if len(prompt + ', ' + detail_str) <= 400:
                prompt += ', ' + detail_str
        
        return prompt
    
    def _compress_level_2(self, prompt: str, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Remove least important elements (margins, some lighting details)"""
        # Get priority order from rules
        priority_rules = self.compression_rules.get('priority', {})
        style_elements = priority_rules.get('style_elements', {}).get('order', [])
        
        # Remove elements in reverse priority order (least important first)
        compressed_prompt = prompt
        
        # Remove margins first (lowest priority)
        if 'margins' in style_elements:
            compressed_prompt = compressed_prompt.replace('margins: white margins', '')
            compressed_prompt = compressed_prompt.replace('white margins', '')
        
        # Remove some lighting details if still too long
        if len(compressed_prompt) > 400 and 'lighting' in style_elements:
            compressed_prompt = compressed_prompt.replace('lighting: ', '')
        
        # Clean up extra commas and spaces
        compressed_prompt = self._clean_prompt(compressed_prompt)
        
        return compressed_prompt
    
    def _compress_level_3(self, prompt: str) -> str:
        """Apply abbreviations from compression rules"""
        abbreviation_rules = self.compression_rules.get('abbreviation', {})
        
        compressed_prompt = prompt
        
        # Apply abbreviations in priority order
        for rule_key, rule_data in abbreviation_rules.items():
            if isinstance(rule_data, dict) and 'short' in rule_data:
                short_form = rule_data['short']
                compressed_prompt = compressed_prompt.replace(rule_key, short_form)
        
        # Clean up extra commas and spaces
        compressed_prompt = self._clean_prompt(compressed_prompt)
        
        return compressed_prompt
    
    def _compress_level_4(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Core concept only - use template if available"""
        template_rules = self.compression_rules.get('template', {})
        
        # Try to find appropriate template
        template_key = 'default'
        if isinstance(style_json, dict):
            medium = style_json.get('medium', '')
            if medium in template_rules:
                template_key = medium
        
        template_data = template_rules.get(template_key, {}).get('base', '[SUBJECT]')
        
        # Replace template placeholders
        prompt = template_data
        prompt = prompt.replace('[SUBJECT]', canonical.subject or 'image')
        prompt = prompt.replace('[STYLE]', canonical.style or 'artistic')
        prompt = prompt.replace('[MOOD]', canonical.mood or 'serene')
        
        # Add style-specific elements if space allows
        if isinstance(style_json, dict) and len(prompt) < 100:
            palette = style_json.get('palette')
            if palette and isinstance(palette, list):
                palette_str = ", ".join(palette[:2])  # Limit to 2 colors
                prompt += f", {palette_str}"
        
        return self._clean_prompt(prompt)
    
    def _clean_prompt(self, prompt: str) -> str:
        """Clean up prompt formatting"""
        import re
        # Remove double commas
        prompt = re.sub(r',\s*,', ',', prompt)
        # Remove leading/trailing commas
        prompt = prompt.strip(', ')
        # Remove double spaces
        prompt = re.sub(r'\s+', ' ', prompt)
        return prompt.strip()
    
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
    
    def render(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
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
    
    def render(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Render canonical prompt for DALL-E 2"""
        # Use DALL-E 3 renderer but with stricter length limits
        dalle3_renderer = DALLE3Renderer(self.model_key, self.constraints)
        prompt = dalle3_renderer.render(canonical, style_json)
        
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

class GPTImage1Renderer(PromptRenderer):
    """Renderer for GPT-Image-1 - similar to DALL-E 3 but optimized for newer model"""
    
    def render(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Render canonical prompt for GPT-Image-1 with style integration"""
        parts = []
        
        # Start with subject (most important)
        if canonical.subject:
            parts.append(canonical.subject)
        else:
            parts.append("an image")
        
        # Add scene context
        if canonical.scene:
            parts.append(f"set in {canonical.scene}")
        
        # Integrate style details from both canonical and style_json
        style_description = self._integrate_style_details(canonical, style_json)
        if style_description:
            parts.append(style_description)
        
        # Add composition
        if canonical.composition:
            parts.append(f"with {canonical.composition} composition")
        
        # Add mood
        if canonical.mood:
            parts.append(f"conveying {canonical.mood}")
        
        # Add lighting
        if canonical.lighting:
            parts.append(f"{canonical.lighting} lighting")
        
        # Add colors
        if canonical.colors:
            color_str = " and ".join(canonical.colors)
            parts.append(f"using {color_str} colors")
        
        # Add keywords naturally
        if canonical.keywords:
            keyword_str = ", ".join(canonical.keywords)
            parts.append(f"featuring {keyword_str}")
        
        # Add constraints as descriptive elements
        if canonical.constraints:
            constraint_str = ", ".join(canonical.constraints)
            parts.append(constraint_str)
        
        # Add negatives from style_json (important style guidelines)
        if isinstance(style_json, dict):
            negatives = style_json.get('negatives')
            if negatives and isinstance(negatives, list):
                negative_descriptions = []
                for negative in negatives:
                    if 'dark colors' in negative.lower():
                        negative_descriptions.append('avoiding dark colors')
                    elif 'saturated colors' in negative.lower():
                        negative_descriptions.append('avoiding saturated colors')
                    elif 'digital appearance' in negative.lower():
                        negative_descriptions.append('avoiding digital appearance')
                    elif 'edge-to-edge' in negative.lower():
                        negative_descriptions.append('avoiding edge-to-edge painting')
                    else:
                        negative_descriptions.append(f'avoiding {negative}')
                
                if negative_descriptions:
                    parts.append(', '.join(negative_descriptions))
        
        # Join with natural connectors
        prompt = ", ".join(parts)
        
        # Clean up grammar
        prompt = self._clean_grammar(prompt)
        
        # GPT-Image-1 can handle much more detail - expand if we have room
        if len(prompt) < 1800:  # More aggressive expansion threshold
            prompt = self._expand_for_gpt_image_1(prompt, canonical, style_json)
        
        return self._enforce_length_limit(prompt)
    
    def _integrate_style_details(self, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Translate JSON style to natural language descriptors"""
        style_parts = []
        
        # Start with canonical style if present
        if canonical.style:
            style_parts.append(canonical.style)
        
        # Add style_json details if available
        if isinstance(style_json, dict):
            # Medium/technique
            medium = style_json.get('medium')
            if medium and medium not in (canonical.style or ''):
                style_parts.append(f"{medium} technique")
            
            # Palette/colors - be more specific about pastel requirements
            palette = style_json.get('palette')
            if palette and isinstance(palette, list):
                palette_str = ", ".join(palette)
                style_parts.append(f"using {palette_str} color palette")
            
            # Brushwork/texture
            brushwork = style_json.get('brushwork')
            if brushwork:
                style_parts.append(f"with {brushwork}")
            
            # Technique details
            technique = style_json.get('technique')
            if technique and technique != medium:
                style_parts.append(f"using {technique}")
            
            # Composition style
            composition_style = style_json.get('composition')
            if composition_style and composition_style != canonical.composition:
                style_parts.append(f"with {composition_style} composition")
            
            # Paper effect
            paper_effect = style_json.get('paper_effect')
            if paper_effect:
                style_parts.append(f"on {paper_effect}")
            
            # Ink details
            ink_details = style_json.get('ink_details')
            if ink_details:
                style_parts.append(f"with {ink_details}")
            
            # Color bleeding
            color_bleeding = style_json.get('color_bleeding')
            if color_bleeding:
                style_parts.append(f"featuring {color_bleeding}")
            
            # Margins - this is critical for watercolor style
            margins = style_json.get('margins')
            if margins:
                style_parts.append(f"with {margins}")
        
        # Combine style elements naturally
        if style_parts:
            if len(style_parts) == 1:
                return f"in {style_parts[0]} style"
            elif len(style_parts) == 2:
                return f"in {style_parts[0]} and {style_parts[1]} style"
            else:
                # For multiple style elements, create rich description
                main_style = style_parts[0]
                additional = ", ".join(style_parts[1:])
                return f"in {main_style} style with {additional}"
        
        return ""
    
    def _expand_for_gpt_image_1(self, prompt: str, canonical: CanonicalPrompt, style_json: dict = None) -> str:
        """Expand prompt with rich details for GPT-Image-1's 2000 char budget"""
        expansions = []
        
        # Add constraints and negatives from style_json
        if isinstance(style_json, dict):
            # Add constraints as positive requirements
            constraints = style_json.get('constraints')
            if constraints and isinstance(constraints, list):
                constraint_descriptions = []
                for constraint in constraints:
                    if 'pastel' in constraint.lower():
                        constraint_descriptions.append('strictly using pastel colors only')
                    elif 'visible brushstrokes' in constraint.lower():
                        constraint_descriptions.append('with clearly visible brushstrokes')
                    elif 'white margins' in constraint.lower():
                        constraint_descriptions.append('with white margins on all sides')
                    elif 'pen and ink' in constraint.lower():
                        constraint_descriptions.append('with pen and ink details')
                    else:
                        constraint_descriptions.append(constraint)
                
                if constraint_descriptions:
                    expansions.append(', '.join(constraint_descriptions))
            
            # Add negatives as explicit exclusions
            negatives = style_json.get('negatives')
            if negatives and isinstance(negatives, list):
                negative_descriptions = []
                for negative in negatives:
                    if 'dark colors' in negative.lower():
                        negative_descriptions.append('avoiding dark colors')
                    elif 'saturated colors' in negative.lower():
                        negative_descriptions.append('avoiding saturated colors')
                    elif 'digital appearance' in negative.lower():
                        negative_descriptions.append('avoiding digital appearance')
                    elif 'edge-to-edge' in negative.lower():
                        negative_descriptions.append('avoiding edge-to-edge painting')
                    else:
                        negative_descriptions.append(f'avoiding {negative}')
                
                if negative_descriptions:
                    expansions.append(', '.join(negative_descriptions))
        
        # Add atmospheric details
        if canonical.mood:
            mood_expansions = {
                'serene': 'creating a tranquil and meditative atmosphere',
                'peaceful': 'evoking a sense of calm and harmony',
                'dramatic': 'building tension and emotional intensity',
                'mysterious': 'suggesting hidden depths and intrigue',
                'nostalgic': 'conveying a sense of longing and memory',
                'energetic': 'bursting with vitality and movement',
                'melancholic': 'imbued with gentle sadness and reflection'
            }
            mood_expansion = mood_expansions.get(canonical.mood.lower())
            if mood_expansion:
                expansions.append(mood_expansion)
        
        # Add texture and material details
        if isinstance(style_json, dict):
            medium = style_json.get('medium', '')
            if medium == 'watercolor':
                expansions.append('with soft, flowing watercolor washes and delicate transparency')
            elif medium == 'oil':
                expansions.append('with rich, impasto brushwork and deep color saturation')
            elif medium == 'ink':
                expansions.append('with precise ink lines and subtle shading')
            elif medium == 'pencil':
                expansions.append('with detailed pencil work and fine crosshatching')
        
        # Add lighting details
        if canonical.lighting:
            lighting_expansions = {
                'golden hour': 'with warm, diffused light creating long shadows and golden tones',
                'sunset': 'bathed in warm orange and pink light with dramatic cloud formations',
                'sunrise': 'with soft, cool light and gentle morning mist',
                'moonlight': 'illuminated by silvery moonlight creating mysterious shadows',
                'daylight': 'with bright, clear natural lighting and crisp details',
                'dramatic': 'with strong contrasts between light and shadow',
                'soft': 'with gentle, even lighting and subtle gradations'
            }
            lighting_expansion = lighting_expansions.get(canonical.lighting.lower())
            if lighting_expansion:
                expansions.append(lighting_expansion)
        
        # Add composition details
        if canonical.composition:
            comp_expansions = {
                'rule of thirds': 'following the rule of thirds for balanced composition',
                'centered': 'with a centered focal point creating symmetry',
                'diagonal': 'using diagonal lines to create dynamic movement',
                'leading lines': 'with leading lines drawing the eye through the scene',
                'framing': 'using natural elements to frame the main subject'
            }
            comp_expansion = comp_expansions.get(canonical.composition.lower())
            if comp_expansion:
                expansions.append(comp_expansion)
        
        # Add color palette details
        if isinstance(style_json, dict) and 'palette' in style_json:
            palette = style_json['palette']
            if isinstance(palette, list) and len(palette) > 0:
                color_desc = ', '.join(palette)
                expansions.append(f'featuring a harmonious color palette of {color_desc}')
        
        # Add brushwork details
        if isinstance(style_json, dict) and 'brushwork' in style_json:
            brushwork = style_json['brushwork']
            brushwork_expansions = {
                'visible brushstrokes': 'with expressive, visible brushstrokes showing the artist\'s hand',
                'fine lines': 'with precise, delicate line work and attention to detail',
                'thick impasto': 'with bold, textured brushwork creating physical depth',
                'smooth': 'with smooth, blended brushwork creating seamless transitions'
            }
            brushwork_expansion = brushwork_expansions.get(brushwork.lower())
            if brushwork_expansion:
                expansions.append(brushwork_expansion)
        
        # Add scene context details
        if canonical.scene:
            scene_expansions = {
                'mountain': 'with majestic mountain peaks and rugged terrain',
                'forest': 'amidst towering trees and dappled sunlight',
                'lake': 'reflecting the surrounding landscape in still waters',
                'ocean': 'with endless horizons and rhythmic waves',
                'city': 'with architectural details and urban atmosphere',
                'garden': 'surrounded by lush vegetation and natural beauty'
            }
            for scene_type, scene_expansion in scene_expansions.items():
                if scene_type in canonical.scene.lower():
                    expansions.append(scene_expansion)
                    break
        
        # Add artistic style details
        if isinstance(style_json, dict) and 'technique' in style_json:
            technique = style_json['technique']
            technique_expansions = {
                'classical': 'in the classical tradition with refined technique',
                'impressionist': 'with impressionistic brushwork capturing light and movement',
                'realistic': 'with photorealistic attention to detail and accuracy',
                'abstract': 'with abstract elements and creative interpretation',
                'minimalist': 'with clean, minimal composition and essential elements'
            }
            technique_expansion = technique_expansions.get(technique.lower())
            if technique_expansion:
                expansions.append(technique_expansion)
        
        # Add more atmospheric and sensory details
        if canonical.subject:
            subject_expansions = {
                'landscape': 'with breathtaking vistas and natural beauty',
                'mountain': 'featuring majestic peaks and dramatic elevation changes',
                'forest': 'with dappled sunlight filtering through ancient trees',
                'lake': 'with crystal-clear waters reflecting the sky above',
                'ocean': 'with endless horizons and rhythmic wave patterns',
                'city': 'with architectural details and urban energy',
                'portrait': 'with expressive features and emotional depth',
                'still life': 'with carefully arranged objects and symbolic meaning'
            }
            for subject_type, subject_expansion in subject_expansions.items():
                if subject_type in canonical.subject.lower():
                    expansions.append(subject_expansion)
                    break
        
        # Add technical quality descriptors
        quality_expansions = [
            'rendered with exceptional attention to detail',
            'showcasing masterful artistic technique',
            'with exquisite color harmony and balance',
            'demonstrating professional artistic skill',
            'with nuanced lighting and shadow work',
            'featuring sophisticated composition and visual flow',
            'with meticulous attention to texture and form',
            'exhibiting refined artistic sensibility',
            'with masterful use of negative space',
            'demonstrating advanced color theory application'
        ]
        
        # Add seasonal or time-based details
        if canonical.scene:
            time_expansions = {
                'sunset': 'with the warm glow of evening light',
                'sunrise': 'bathed in the soft light of dawn',
                'noon': 'under bright, clear daylight',
                'night': 'illuminated by moonlight and stars',
                'autumn': 'with rich fall colors and golden light',
                'spring': 'with fresh, vibrant colors of renewal',
                'summer': 'with warm, saturated summer tones',
                'winter': 'with cool, crisp winter atmosphere'
            }
            for time_type, time_expansion in time_expansions.items():
                if time_type in canonical.scene.lower():
                    expansions.append(time_expansion)
                    break
        
        # Combine expansions
        if expansions:
            # Add expansions in a natural way
            expanded_prompt = prompt
            
            # Add quality descriptors first (they're always valuable)
            for quality_desc in quality_expansions:
                if len(expanded_prompt + ', ' + quality_desc) < 1950:
                    expanded_prompt += ', ' + quality_desc
                else:
                    break
            
            # Then add other expansions
            for expansion in expansions:
                if len(expanded_prompt + ', ' + expansion) < 1950:  # Leave some buffer
                    expanded_prompt += ', ' + expansion
            
            return expanded_prompt
        
        return prompt
    
    def _clean_grammar(self, prompt: str) -> str:
        """Clean up grammar and flow"""
        import re
        # Remove double spaces
        prompt = re.sub(r'\s+', ' ', prompt)
        # Remove trailing commas
        prompt = re.sub(r',\s*$', '', prompt)
        return prompt.strip()

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
        elif model_key == 'gpt-image-1':
            return GPTImage1Renderer(model_key, constraints)
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
