#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, '/Users/autojenny/Documents/projects/blog')
from member_design_description_generator import MemberDesignDescriptionGenerator

# Test the fixed JSON parsing with markdown code blocks
generator = MemberDesignDescriptionGenerator(dry_run=True)

# Test with the actual LLM response format including markdown
json_response = '''```json
{
  "descriptions": [
    {
      "tartan_id": 6312,
      "tartan_name": "Haltom City Fire Rescue Member Design",
      "description": {
        "text": "This tartan is a Member Design created using the Clan Tartan Designer, available at https://clan.com/tartandesigner/. The design has been published and produced as a physical product."
      }
    }
  ]
}
```'''

tartan_group = [{'id': 6312, 'name': 'Haltom City Fire Rescue Member Design  2'}]

descriptions = generator.parse_llm_response(json_response, tartan_group)
print('FIXED MARKDOWN JSON PARSING RESULT:')
print(f'Found descriptions: {len(descriptions)}')
for tartan_id, desc in descriptions.items():
    print(f'ID {tartan_id}: {desc[:200]}...')
