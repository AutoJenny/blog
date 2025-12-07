#!/usr/bin/env python3
"""
Regenerate family research data based on feedback.

Uses LLM to decide whether to:
1. Regenerate entire research (web research + story facts) - for major issues
2. Just fix narrative with OpenAI - for minor issues

Usage:
    python3 scripts/regenerate_with_feedback.py <family_id> "<feedback text>"
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager
from config.unified_config import get_config

# Import LLM service
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
    from app.llm.services import LLMService
except ImportError:
    try:
        from blueprints.planning_llm import LLMService
    except ImportError:
        LLMService = None


def analyze_feedback(family_name: str, feedback: str, llm_service) -> dict:
    """Use LLM to analyze feedback and decide on action."""
    
    prompt = f"""You are analyzing feedback about a historical narrative for the {family_name} family/clan.

Feedback from user:
"{feedback}"

Based on this feedback, determine:
1. Severity: "major" or "minor"
   - "major" = fundamental issues requiring new research (factual errors, missing key information, wrong focus)
   - "minor" = style, tone, or refinement issues that can be fixed in the narrative

2. Action: "regenerate" or "refine"
   - "regenerate" = need to redo web research and story facts (for major issues)
   - "refine" = can fix with OpenAI fact-checking with additional instructions (for minor issues)

3. Instructions: Specific guidance for the chosen action

Respond in JSON format:
{{
    "severity": "major" or "minor",
    "action": "regenerate" or "refine",
    "reasoning": "brief explanation",
    "instructions": "specific instructions for the chosen action"
}}"""

    try:
        # Handle different LLMService interfaces
        if hasattr(llm_service, 'generate'):
            response = llm_service.generate(
                prompt=prompt,
                model_name='llama3.2:latest',
                temperature=0.2,
                max_tokens=500
            )
        elif hasattr(llm_service, 'execute_llm_request'):
            messages = [
                {"role": "system", "content": "You are a helpful assistant that analyzes feedback and returns JSON."},
                {"role": "user", "content": prompt}
            ]
            result = llm_service.execute_llm_request(
                provider='ollama',
                model='llama3.2:latest',
                messages=messages,
                max_tokens=500,
                temperature=0.2
            )
            if 'error' in result:
                raise Exception(result['error'])
            response = result.get('content', '')
        else:
            raise Exception("LLMService interface not supported")
        
        # Extract JSON from response
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result
        else:
            # Fallback: try to parse as JSON directly
            return json.loads(response)
    except Exception as e:
        print(f"Error analyzing feedback: {e}")
        # Default to refine for safety
        return {
            "severity": "minor",
            "action": "refine",
            "reasoning": "Could not analyze feedback, defaulting to refine",
            "instructions": feedback
        }


def regenerate_full(family_id: int, family_name: str, instructions: str):
    """Regenerate entire research process."""
    print(f"Regenerating full research for {family_name} (ID: {family_id})...")
    print(f"Instructions: {instructions}")
    
    scripts_dir = Path(__file__).parent
    
    # Step 1: Web research
    print("\n[1/3] Running web research...")
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'research_family_web.py'), str(family_id), '--save'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error in web research: {result.stderr}")
        return False
    
    # Step 2: Story facts
    print("\n[2/3] Running story facts research...")
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'research_family_story_facts.py'), 
         str(family_id), '--save', '--word-target', '3000'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error in story facts: {result.stderr}")
        return False
    
    # Step 3: Fact-checking
    print("\n[3/3] Running fact-checking...")
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'fact_check_narrative.py'), 
         str(family_id), '--update-db'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error in fact-checking: {result.stderr}")
        return False
    
    return True


def refine_narrative(family_id: int, family_name: str, instructions: str):
    """Refine narrative with OpenAI using additional instructions."""
    print(f"Refining narrative for {family_name} (ID: {family_id})...")
    print(f"Additional instructions: {instructions}")
    
    scripts_dir = Path(__file__).parent
    
    print("\nSending to OpenAI with custom instructions...")
    
    result = subprocess.run(
        [sys.executable, str(scripts_dir / 'fact_check_narrative.py'), 
         str(family_id), '--update-db', '--custom-instructions', instructions],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    print(result.stdout)
    return True


def main():
    parser = argparse.ArgumentParser(description='Regenerate family research based on feedback')
    parser.add_argument('family_id', type=int, help='Family ID')
    parser.add_argument('feedback', type=str, help='Feedback text')
    parser.add_argument('--force-action', choices=['regenerate', 'refine'], 
                       help='Force a specific action without LLM analysis')
    
    args = parser.parse_args()
    
    # Get family info
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM families WHERE id = %s", (args.family_id,))
            family = cur.fetchone()
            if not family:
                print(f"Error: Family ID {args.family_id} not found")
                sys.exit(1)
            
            family_name = family['name']
    
    print("=" * 60)
    print(f"Feedback Analysis: {family_name} (ID: {args.family_id})")
    print("=" * 60)
    print(f"Feedback: {args.feedback}")
    print()
    
    if args.force_action:
        action = args.force_action
        print(f"Force action: {action}")
        instructions = args.feedback
    else:
        # Analyze feedback with LLM
        if LLMService is None:
            print("Warning: LLMService not available, defaulting to 'refine' action")
            print("(To force regenerate, use: --force-action regenerate)")
            action = 'refine'
            instructions = args.feedback
        else:
            print("Analyzing feedback with LLM...")
            try:
                llm_service = LLMService()
                analysis = analyze_feedback(family_name, args.feedback, llm_service)
                
                print(f"\nAnalysis:")
                print(f"  Severity: {analysis['severity']}")
                print(f"  Action: {analysis['action']}")
                print(f"  Reasoning: {analysis['reasoning']}")
                print(f"  Instructions: {analysis['instructions']}")
                print()
                
                action = analysis['action']
                instructions = analysis['instructions']
            except Exception as e:
                print(f"Error analyzing feedback with LLM: {e}")
                print("Defaulting to 'refine' action")
                action = 'refine'
                instructions = args.feedback
    
    # Execute action
    report = {
        'action_taken': action,
        'severity': analysis.get('severity', 'minor') if not args.force_action else 'unknown',
        'reasoning': analysis.get('reasoning', '') if not args.force_action else 'Forced action',
        'instructions_used': instructions if not args.force_action else args.feedback,
        'steps_completed': [],
        'steps_failed': [],
        'summary': ''
    }
    
    if action == 'regenerate':
        success = regenerate_full(args.family_id, family_name, instructions if not args.force_action else args.feedback)
        if success:
            report['steps_completed'] = ['Web Research', 'Story Facts & Narrative', 'Fact-Checking with OpenAI']
            report['summary'] = f"Successfully regenerated complete research for {family_name}. All three stages completed: (1) Web research gathered new data, (2) Story facts extracted and narrative compiled, (3) Narrative fact-checked and refined by OpenAI."
        else:
            report['steps_failed'] = ['One or more regeneration steps failed']
            report['summary'] = f"Failed to complete full regeneration for {family_name}. Check error messages above."
    else:
        success = refine_narrative(args.family_id, family_name, instructions if not args.force_action else args.feedback)
        if success:
            report['steps_completed'] = ['Narrative Refinement with OpenAI']
            report['summary'] = f"Successfully refined the narrative for {family_name} using OpenAI with your specific feedback. The narrative has been updated to address: {instructions if not args.force_action else args.feedback}"
        else:
            report['steps_failed'] = ['Narrative refinement failed']
            report['summary'] = f"Failed to refine narrative for {family_name}. Check error messages above."
    
    # Output JSON report at the end (for API parsing)
    import json
    print("\n" + "="*60)
    print("FEEDBACK_PROCESSING_REPORT_START")
    print(json.dumps(report, indent=2))
    print("FEEDBACK_PROCESSING_REPORT_END")
    print("="*60)
    
    if success:
        print(f"\n✓ Successfully processed {family_name}")
    else:
        print(f"\n✗ Failed to process {family_name}")
        sys.exit(1)


if __name__ == '__main__':
    main()

