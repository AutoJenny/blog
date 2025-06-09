"""LLM action configuration for idea generation."""

from typing import Dict, Any
from ..base import BaseAction

class IdeaGenerationAction(BaseAction):
    """Action for generating a basic idea from an idea seed."""
    
    def __init__(self):
        super().__init__({
            'name': 'idea_generation',
            'description': 'Generate a basic idea from an idea seed',
            'input_fields': ['idea_seed'],
            'output_fields': ['basic_idea'],
            'prompt_template': """[system] You are an expert in Scottish history and culture, dedicated to accuracy and authenticity in everything you do. You adhere to academic values, but love to popularise ideas to make them easily understandable to those with no knowledge of your specialism.

[system] Expand the following short idea into a paragraph-length brief for a long-form blog article. The brief should outline the scope, angle, tone, and core ideas that could be developed into a full article. Use clear, engaging language.

Short Idea:
[data:idea_seed]

Your response should:
1. Focus specifically on Scottish cultural and historical aspects
2. Maintain academic accuracy while being accessible
3. Suggest clear angles and themes for development
4. Use UK-British spellings and idioms
5. Return only the expanded brief, with no additional commentary or formatting""",
            'temperature': 0.7,
            'max_tokens': 1000
        })
    
    def process_output(self, output: str) -> Dict[str, Any]:
        """Process the LLM output into the required format."""
        return {'result': output.strip()} 