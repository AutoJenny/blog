UPDATE llm_action 
SET prompt_template = 'Create a structured outline for a blog post with the following details:

Title: {{title}}
Basic Idea: {{idea}}
Interesting Facts:
{{#each facts}}
- {{this}}
{{/each}}

IMPORTANT: Your response must be a valid JSON array. Do not include any other text or explanation.

Example format:
[
  {
    "heading": "Introduction",
    "theme": "Setting the context and importance",
    "facts": ["Fact 1"],
    "ideas": ["Key point 1"]
  },
  {
    "heading": "Main Section",
    "theme": "Core topic exploration",
    "facts": ["Fact 2"],
    "ideas": ["Key point 2"]
  }
]

Please provide your response in exactly this format, with no additional text.'
WHERE field_name = 'section_structure_creator'; 