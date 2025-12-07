#!/usr/bin/env python3
"""
Audit blockquote elements in OpenAI-generated narratives.

For each family that has <blockquote> elements in their narrative_fact_checked,
this script:
  - Extracts all blockquote content
  - Uses the local LLM to determine if each blockquote is:
    * A proper quotation (actual quoted text from a source)
    * Contextual text (explanatory text that shouldn't be in blockquote)
    * A placeholder (e.g., "[Insert the actual quoted verse here...]")
    * Other inappropriate content
  - Records the results in a JSON file for review

Usage:
    python3 scripts/audit_blockquotes.py [--limit N] [--output FILE]
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Optional, List, Dict
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.database import db_manager

# Import LLM service
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blog-core'))
    from app.llm.services import LLMService
except ImportError:
    try:
        from blueprints.planning_llm import LLMService
    except ImportError:
        LLMService = None


def get_families_with_blockquotes(limit: Optional[int] = None):
    """Fetch families that have blockquote elements in their narrative_fact_checked."""
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT
                    f.id,
                    f.name,
                    f.research_data->'metadata'->>'narrative_fact_checked' AS narrative
                FROM families f
                WHERE research_data IS NOT NULL
                  AND research_data ? 'metadata'
                  AND research_data->'metadata' ? 'narrative_fact_checked'
                  AND POSITION('<blockquote' IN (research_data->'metadata'->>'narrative_fact_checked')) > 0
                ORDER BY f.id
            """
            if limit is not None:
                query += " LIMIT %s"
                cur.execute(query, (limit,))
            else:
                cur.execute(query)
            return cur.fetchall()


def extract_blockquotes(html_content: str) -> List[Dict[str, str]]:
    """Extract all blockquote elements and their content."""
    if not html_content:
        return []
    
    blockquotes = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for i, bq in enumerate(soup.find_all('blockquote'), 1):
        # Get text content, preserving some structure
        text = bq.get_text(separator=' ', strip=True)
        # Get raw HTML for context
        raw_html = str(bq)
        
        blockquotes.append({
            'index': i,
            'text': text,
            'raw_html': raw_html,
            'length': len(text)
        })
    
    return blockquotes


def build_audit_prompt(family_name: str, blockquote_text: str, narrative_context: str) -> str:
    """Build a prompt asking the LLM to evaluate if a blockquote is appropriate."""
    prompt = f"""You are auditing HTML content for proper use of <blockquote> elements.

The <blockquote> HTML element should ONLY be used for actual quotations—text that is directly quoted from a source (e.g., historical documents, poems, songs, official records, or other primary sources).

It should NOT be used for:
- Contextual or explanatory text
- Placeholder text (e.g., "[Insert the actual quoted verse here...]")
- Summaries or paraphrases
- General narrative text that happens to be about quotes

Family name: {family_name}

Here is the blockquote content to evaluate:
<<<BLOCKQUOTE
{blockquote_text}
>>>

Here is the surrounding narrative context (for reference):
<<<CONTEXT
{narrative_context[:500]}
>>>

Your task:
1. Determine if this blockquote contains:
   A) A proper quotation (actual quoted text from a source)
   B) Contextual/explanatory text (should not be in blockquote)
   C) A placeholder (e.g., "[Insert...]" or similar incomplete text)
   D) Other inappropriate content

2. Provide a brief explanation (1-2 sentences) of your assessment.

Respond in this exact JSON format:
{{
  "classification": "A" | "B" | "C" | "D",
  "explanation": "brief explanation here",
  "needs_review": true | false
}}

Set "needs_review" to true if:
- Classification is B, C, or D (not a proper quotation)
- You are uncertain about the classification
- The blockquote appears to be a placeholder or incomplete

Set "needs_review" to false only if it's clearly a proper quotation (A) with no issues."""
    return prompt


def audit_blockquote(llm_service, family_name: str, blockquote_text: str, narrative_context: str) -> Optional[Dict]:
    """Use the local LLM to audit a single blockquote."""
    prompt = build_audit_prompt(family_name, blockquote_text, narrative_context)
    
    try:
        response = None
        
        # Preferred path: blog-core LLMService with .generate using Ollama
        if hasattr(llm_service, "generate"):
            response = llm_service.generate(
                prompt=prompt,
                model_name=os.environ.get("DEFAULT_LLM_MODEL", "mistral"),
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=200,
            )
        # Fallback: planning_llm LLMService with execute_llm_request using Ollama chat API
        elif hasattr(llm_service, "execute_llm_request"):
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
            result = llm_service.execute_llm_request(
                provider="ollama",
                model="llama3.2",
                messages=messages,
                max_tokens=200,
                temperature=0.1,
            )
            if "error" in result:
                print(f"  Error from LLM service: {result['error']}")
                return None
            response = result.get("content", "")
        else:
            print("  Error: LLMService interface not supported")
            return None
        
        if not response:
            return None
        
        # Try to extract JSON from response
        response = response.strip()
        
        # Look for JSON in the response (might be wrapped in markdown code blocks)
        json_match = re.search(r'\{[^{}]*"classification"[^{}]*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to find JSON-like structure
            json_str = response
        
        try:
            result = json.loads(json_str)
            # Validate structure
            if "classification" not in result:
                return None
            if result["classification"] not in ["A", "B", "C", "D"]:
                return None
            return result
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract classification manually
            classification_match = re.search(r'"classification"\s*:\s*"([ABCD])"', response)
            explanation_match = re.search(r'"explanation"\s*:\s*"([^"]+)"', response)
            needs_review_match = re.search(r'"needs_review"\s*:\s*(true|false)', response, re.IGNORECASE)
            
            if classification_match:
                result = {
                    "classification": classification_match.group(1),
                    "explanation": explanation_match.group(1) if explanation_match else "Could not parse explanation",
                    "needs_review": needs_review_match.group(1).lower() == "true" if needs_review_match else True
                }
                return result
            return None
            
    except Exception as e:
        print(f"  Error during LLM audit: {e}")
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Audit blockquote elements in OpenAI narratives"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of families to process (for testing)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/blockquote_audit_results.json",
        help="Output JSON file path (default: data/blockquote_audit_results.json)",
    )
    
    args = parser.parse_args()
    
    if LLMService is None:
        print("Error: LLMService could not be imported. Cannot audit blockquotes.")
        sys.exit(1)
    
    # LLMService reads configuration from environment; no config object needed
    llm_service = LLMService()
    
    families = get_families_with_blockquotes(limit=args.limit)
    total = len(families)
    
    print("\n" + "=" * 60)
    print("Audit blockquote elements in OpenAI narratives")
    print("=" * 60)
    print(f"Families to process: {total}")
    print(f"Output file: {args.output}")
    print()
    
    results = {
        "total_families": total,
        "total_blockquotes": 0,
        "needs_review_count": 0,
        "classification_counts": {
            "A": 0,  # Proper quotation
            "B": 0,  # Contextual text
            "C": 0,  # Placeholder
            "D": 0,  # Other inappropriate
        },
        "families": []
    }
    
    for i, row in enumerate(families, 1):
        family_id = row["id"]
        family_name = row["name"]
        narrative = row["narrative"] or ""
        
        print(f"[{i}/{total}] {family_name} (ID: {family_id})")
        
        if not narrative.strip():
            print("  Skipping: narrative_fact_checked is empty")
            continue
        
        blockquotes = extract_blockquotes(narrative)
        if not blockquotes:
            print("  No blockquotes found (unexpected)")
            continue
        
        print(f"  Found {len(blockquotes)} blockquote(s)")
        results["total_blockquotes"] += len(blockquotes)
        
        family_result = {
            "family_id": family_id,
            "family_name": family_name,
            "blockquote_count": len(blockquotes),
            "needs_review": False,
            "blockquotes": []
        }
        
        for bq in blockquotes:
            print(f"    Auditing blockquote {bq['index']} ({bq['length']} chars)...")
            
            # Get a snippet of narrative context around the blockquote
            # Find the position of this blockquote in the narrative
            bq_pos = narrative.find(bq['raw_html'])
            context_start = max(0, bq_pos - 250)
            context_end = min(len(narrative), bq_pos + len(bq['raw_html']) + 250)
            context = narrative[context_start:context_end]
            
            audit_result = audit_blockquote(llm_service, family_name, bq['text'], context)
            
            if audit_result:
                classification = audit_result["classification"]
                results["classification_counts"][classification] += 1
                
                if audit_result.get("needs_review", False):
                    family_result["needs_review"] = True
                    results["needs_review_count"] += 1
                
                bq_result = {
                    "index": bq['index'],
                    "text": bq['text'][:200] + ("..." if len(bq['text']) > 200 else ""),  # Truncate for readability
                    "length": bq['length'],
                    "classification": classification,
                    "explanation": audit_result.get("explanation", ""),
                    "needs_review": audit_result.get("needs_review", False)
                }
                family_result["blockquotes"].append(bq_result)
                
                status = "✓" if classification == "A" and not audit_result.get("needs_review", False) else "⚠"
                print(f"      {status} Classification: {classification} ({'needs review' if audit_result.get('needs_review') else 'OK'})")
            else:
                print(f"      ✗ Failed to audit blockquote")
                bq_result = {
                    "index": bq['index'],
                    "text": bq['text'][:200] + ("..." if len(bq['text']) > 200 else ""),
                    "length": bq['length'],
                    "classification": "ERROR",
                    "explanation": "Failed to get LLM response",
                    "needs_review": True
                }
                family_result["blockquotes"].append(bq_result)
                family_result["needs_review"] = True
                results["needs_review_count"] += 1
        
        if family_result["needs_review"]:
            results["families"].append(family_result)
    
    # Save results to JSON file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("Audit complete")
    print("=" * 60)
    print(f"Total families processed: {total}")
    print(f"Total blockquotes found: {results['total_blockquotes']}")
    print(f"Blockquotes needing review: {results['needs_review_count']}")
    print(f"\nClassification breakdown:")
    print(f"  A (Proper quotation): {results['classification_counts']['A']}")
    print(f"  B (Contextual text): {results['classification_counts']['B']}")
    print(f"  C (Placeholder): {results['classification_counts']['C']}")
    print(f"  D (Other inappropriate): {results['classification_counts']['D']}")
    print(f"\nFamilies needing review: {len(results['families'])}")
    print(f"\nResults saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

