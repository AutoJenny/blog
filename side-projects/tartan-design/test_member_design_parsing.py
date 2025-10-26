#!/usr/bin/env python3
"""
Test script to see what the LLM is generating for failed Member Design cases
"""

import sys
from pathlib import Path
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import db_manager
from blueprints.planning_llm import LLMService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llm_response():
    llm_service = LLMService()
    
    # Test with a failed case
    tartan_name = "Von Prondzynski Member Design"
    
    system_prompt = """You are a tartan expert and creative writer specialising in Scottish textile traditions. You understand the significance of modern tartan design tools and can craft engaging descriptions that accurately represent the origin and characteristics of Member Design tartans.

CRITICAL: Use UK English spellings throughout (colours, centre, honour, etc.)"""

    user_prompt = f"""Generate descriptions for these Member Design tartans:

  - ID 6508: '{tartan_name}'

IMPORTANT CONTEXT:
These tartans are "Member Designs" - they were created using the Clan Tartan Designer at <a href="https://clan.com/tartandesigner/">https://clan.com/tartandesigner/</a> and have been published by their designers and subsequently produced as physical products.

The base name element 'Von Prondzynski' could refer to either:
- A SURNAME (family/clan name): Focus on family heritage, clan history, ancestral connections, and traditional family associations
- A PLACE NAME (geographical location): Focus on landscape, regional characteristics, local history, geographical features, and area-specific traditions
- A THEME OR CONCEPT: Focus on the symbolic meaning, cultural significance, or intended purpose

TASK:
Create unique, engaging descriptions for each tartan that:
1. Clearly state that this is a Member Design created using the Clan Tartan Designer
2. Include the HTML link to https://clan.com/tartandesigner/
3. Explain that the design has been published and produced as physical product
4. Make an educated guess about the tartan's meaning based on the name element
5. Clearly indicate this interpretation is speculative ("likely represents", "probably inspired by", "suggests", etc.)
6. Describe the visual characteristics and colour scheme
7. Explain the cultural significance or intended use

OUTPUT FORMAT:
For each tartan, provide a description starting with the tartan name, followed by your description.

Focus on:
- Clear identification as a Member Design with proper attribution
- Speculative interpretation of the name element (surname, place, or theme)
- Visual characteristics and colour palette
- Cultural significance and intended purpose
- Professional, informative tone while acknowledging uncertainty

Remember: Use UK English spellings throughout (colours, centre, honour, etc.)"""

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    try:
        response = llm_service.execute_llm_request('ollama', 'llama3.2:latest', messages, max_tokens=2000)
        
        if response and 'content' in response:
            generated_description = response['content']
            print("=" * 80)
            print("RAW LLM RESPONSE:")
            print("=" * 80)
            print(generated_description)
            print("=" * 80)
            print(f"Response length: {len(generated_description)} characters")
            
            # Test the parsing
            lines = generated_description.strip().split('\n')
            print("\nPARSING TEST:")
            print("=" * 40)
            for i, line in enumerate(lines):
                line = line.strip()
                print(f"Line {i+1}: {line}")
                if tartan_name.lower() in line.lower():
                    print(f"  ^^^ FOUND TARTAN NAME HERE")
                elif "von prondzynski" in line.lower():
                    print(f"  ^^^ FOUND SIMPLIFIED NAME HERE")
        else:
            print(f"Failed to generate response: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"LLM request failed: {e}")

if __name__ == "__main__":
    test_llm_response()
