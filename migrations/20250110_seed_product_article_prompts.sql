-- Migration: Seed Product Article CLAN-First Prompt Templates
-- Date: 2025-01-10
-- Purpose: Add CLAN-first prompt templates for product article generation

-- Product Article Topic Brainstorming Template
INSERT INTO llm_prompt (name, description, system_prompt, prompt_text, parameters)
SELECT 
    'product_article_topic_brainstorming',
    'Generate topics for product article from CLAN data and standard sections',
    'You are a content strategist for CLAN.com, a Scottish heritage and culture website. Generate engaging topics for product articles that prioritize CLAN''s own product data and maintain CLAN''s warm, professional Scottish tone.',
    'You are brainstorming topics for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== STANDARD SECTION TEMPLATE ===
The article must follow this rigid 7-section structure:
1. Introduction & Historical Context
2. Craftsmanship & Materials
3. Features & Specifications
4. How to Use / Practical Guide
5. Benefits & Value
6. Alternative Products
7. Conclusion

=== REQUIREMENTS ===
1. Generate 3-5 specific topics for EACH of the 7 sections
2. Prioritize topics that can be answered using CLAN data
3. For sections where CLAN data is missing or insufficient (< 50 words), suggest topics that LLM can supplement
4. Mark topics that require LLM supplementation with [GENERAL KNOWLEDGE] tag
5. Ensure topics are specific to this product, not generic
6. Maintain CLAN''s warm, professional Scottish tone

=== OUTPUT FORMAT ===
Return a JSON object with this structure:
{{
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction & Historical Context",
      "topics": [
        "Topic 1 (from CLAN data)",
        "Topic 2 (from CLAN data)",
        "Topic 3 [GENERAL KNOWLEDGE]"
      ]
    }},
    {{
      "section_number": 2,
      "section_name": "Craftsmanship & Materials",
      "topics": [...]
    }},
    ...
  ]
}}',
    '{"model": "llama3.2:latest", "temperature": 0.7, "max_tokens": 3000}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = 'product_article_topic_brainstorming'
);

UPDATE llm_prompt SET
    description = 'Generate topics for product article from CLAN data and standard sections',
    system_prompt = 'You are a content strategist for CLAN.com, a Scottish heritage and culture website. Generate engaging topics for product articles that prioritize CLAN''s own product data and maintain CLAN''s warm, professional Scottish tone.',
    prompt_text = 'You are brainstorming topics for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== STANDARD SECTION TEMPLATE ===
The article must follow this rigid 7-section structure:
1. Introduction & Historical Context
2. Craftsmanship & Materials
3. Features & Specifications
4. How to Use / Practical Guide
5. Benefits & Value
6. Alternative Products
7. Conclusion

=== REQUIREMENTS ===
1. Generate 3-5 specific topics for EACH of the 7 sections
2. Prioritize topics that can be answered using CLAN data
3. For sections where CLAN data is missing or insufficient (< 50 words), suggest topics that LLM can supplement
4. Mark topics that require LLM supplementation with [GENERAL KNOWLEDGE] tag
5. Ensure topics are specific to this product, not generic
6. Maintain CLAN''s warm, professional Scottish tone

=== OUTPUT FORMAT ===
Return a JSON object with this structure:
{{
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction & Historical Context",
      "topics": [
        "Topic 1 (from CLAN data)",
        "Topic 2 (from CLAN data)",
        "Topic 3 [GENERAL KNOWLEDGE]"
      ]
    }},
    {{
      "section_number": 2,
      "section_name": "Craftsmanship & Materials",
      "topics": [...]
    }},
    ...
  ]
}}',
    parameters = '{"model": "llama3.2:latest", "temperature": 0.7, "max_tokens": 3000}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'product_article_topic_brainstorming';

-- Product Article Section Structure Template
INSERT INTO llm_prompt (name, description, system_prompt, prompt_text, parameters)
SELECT 
    'product_article_section_structure',
    'Design section structure for product article (template-based, CLAN data prioritized)',
    'You are a content strategist for CLAN.com. Design the section structure for a product article, ensuring it follows the rigid 7-section template while prioritizing CLAN data.',
    'You are designing the section structure for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== RIGID SECTION TEMPLATE ===
The article MUST follow this exact 7-section structure (cannot be changed):
1. Introduction & Historical Context
2. Craftsmanship & Materials
3. Features & Specifications
4. How to Use / Practical Guide
5. Benefits & Value
6. Alternative Products (ALWAYS include 3-5 alternatives)
7. Conclusion

=== ALTERNATIVE PRODUCTS DATA ===
{alternative_products_data}

=== REQUIREMENTS ===
1. Confirm the 7-section structure (it is fixed and cannot be modified)
2. For each section, indicate which CLAN data fields will be used
3. Mark sections that will need LLM supplementation (where CLAN data is missing or < 50 words)
4. For Alternative Products section, specify which discovery strategies will be used (same category, vector search, price-based, same supplier)

=== OUTPUT FORMAT ===
Return a JSON object confirming the structure:
{{
  "structure_confirmed": true,
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction & Historical Context",
      "clan_data_sources": ["heritage_data.historical_origins"],
      "needs_llm_supplement": false,
      "estimated_word_count": 200
    }},
    ...
  ],
  "alternative_products": {{
    "strategy": "same_category, vector_search, price-based",
    "count": 5
  }}
}}',
    '{"model": "llama3.2:latest", "temperature": 0.5, "max_tokens": 2000}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = 'product_article_section_structure'
);

UPDATE llm_prompt SET
    description = 'Design section structure for product article (template-based, CLAN data prioritized)',
    system_prompt = 'You are a content strategist for CLAN.com. Design the section structure for a product article, ensuring it follows the rigid 7-section template while prioritizing CLAN data.',
    prompt_text = 'You are designing the section structure for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== RIGID SECTION TEMPLATE ===
The article MUST follow this exact 7-section structure (cannot be changed):
1. Introduction & Historical Context
2. Craftsmanship & Materials
3. Features & Specifications
4. How to Use / Practical Guide
5. Benefits & Value
6. Alternative Products (ALWAYS include 3-5 alternatives)
7. Conclusion

=== ALTERNATIVE PRODUCTS DATA ===
{alternative_products_data}

=== REQUIREMENTS ===
1. Confirm the 7-section structure (it is fixed and cannot be modified)
2. For each section, indicate which CLAN data fields will be used
3. Mark sections that will need LLM supplementation (where CLAN data is missing or < 50 words)
4. For Alternative Products section, specify which discovery strategies will be used (same category, vector search, price-based, same supplier)

=== OUTPUT FORMAT ===
Return a JSON object confirming the structure:
{{
  "structure_confirmed": true,
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction & Historical Context",
      "clan_data_sources": ["heritage_data.historical_origins"],
      "needs_llm_supplement": false,
      "estimated_word_count": 200
    }},
    ...
  ],
  "alternative_products": {{
    "strategy": "same_category, vector_search, price-based",
    "count": 5
  }}
}}',
    parameters = '{"model": "llama3.2:latest", "temperature": 0.5, "max_tokens": 2000}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'product_article_section_structure';

-- Product Article Section Ideas Template
INSERT INTO llm_prompt (name, description, system_prompt, prompt_text, parameters)
SELECT 
    'product_article_section_ideas',
    'Generate section-specific ideas for product article (CLAN data first)',
    'You are a content writer for CLAN.com. Generate specific ideas and talking points for each section of a product article, prioritizing CLAN data over general knowledge.',
    'You are generating ideas for a specific section of a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== CURRENT SECTION ===
Section: {section_name}
Section Number: {section_number}
Section Topics: {section_topics}

=== REQUIREMENTS ===
1. Generate 5-8 specific ideas/talking points for this section
2. Prioritize ideas that can be answered using CLAN data
3. For each idea, indicate the CLAN data source (e.g., "product.description", "supplier_description")
4. Mark ideas that require LLM supplementation with [GENERAL KNOWLEDGE] tag
5. Ensure ideas are specific to this product, not generic
6. Maintain CLAN''s warm, professional Scottish tone

=== OUTPUT FORMAT ===
Return a JSON object:
{{
  "section_number": {section_number},
  "section_name": "{section_name}",
  "ideas": [
    {{
      "idea": "Specific idea or talking point",
      "clan_data_source": "product.description",
      "needs_llm_supplement": false
    }},
    {{
      "idea": "Another idea [GENERAL KNOWLEDGE]",
      "clan_data_source": null,
      "needs_llm_supplement": true
    }},
    ...
  ]
}}',
    '{"model": "llama3.2:latest", "temperature": 0.7, "max_tokens": 2000}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = 'product_article_section_ideas'
);

UPDATE llm_prompt SET
    description = 'Generate section-specific ideas for product article (CLAN data first)',
    system_prompt = 'You are a content writer for CLAN.com. Generate specific ideas and talking points for each section of a product article, prioritizing CLAN data over general knowledge.',
    prompt_text = 'You are generating ideas for a specific section of a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== CURRENT SECTION ===
Section: {section_name}
Section Number: {section_number}
Section Topics: {section_topics}

=== REQUIREMENTS ===
1. Generate 5-8 specific ideas/talking points for this section
2. Prioritize ideas that can be answered using CLAN data
3. For each idea, indicate the CLAN data source (e.g., "product.description", "supplier_description")
4. Mark ideas that require LLM supplementation with [GENERAL KNOWLEDGE] tag
5. Ensure ideas are specific to this product, not generic
6. Maintain CLAN''s warm, professional Scottish tone

=== OUTPUT FORMAT ===
Return a JSON object:
{{
  "section_number": {section_number},
  "section_name": "{section_name}",
  "ideas": [
    {{
      "idea": "Specific idea or talking point",
      "clan_data_source": "product.description",
      "needs_llm_supplement": false
    }},
    {{
      "idea": "Another idea [GENERAL KNOWLEDGE]",
      "clan_data_source": null,
      "needs_llm_supplement": true
    }},
    ...
  ]
}}',
    parameters = '{"model": "llama3.2:latest", "temperature": 0.7, "max_tokens": 2000}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'product_article_section_ideas';

-- Product Article Section Titling Template
INSERT INTO llm_prompt (name, description, system_prompt, prompt_text, parameters)
SELECT 
    'product_article_section_titling',
    'Finalize section titles for product article (CLAN terminology preferred)',
    'You are a content editor for CLAN.com. Create engaging, SEO-friendly section titles that use CLAN terminology and product names when possible.',
    'You are finalizing section titles for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
Product Name: {product_name}
Product Category: {category_name}
Supplier Name: {supplier_name}

=== SECTIONS TO TITLE ===
{sections_with_ideas}

=== REQUIREMENTS ===
1. Create engaging, SEO-friendly titles for each section
2. Use CLAN product name and terminology when appropriate
3. Titles should be 5-12 words
4. Maintain CLAN''s warm, professional Scottish tone
5. Ensure titles accurately reflect section content

=== OUTPUT FORMAT ===
Return a JSON object:
{{
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction & Historical Context",
      "title": "Engaging title using product name"
    }},
    ...
  ]
}}',
    '{"model": "llama3.2:latest", "temperature": 0.6, "max_tokens": 1500}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = 'product_article_section_titling'
);

UPDATE llm_prompt SET
    description = 'Finalize section titles for product article (CLAN terminology preferred)',
    system_prompt = 'You are a content editor for CLAN.com. Create engaging, SEO-friendly section titles that use CLAN terminology and product names when possible.',
    prompt_text = 'You are finalizing section titles for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
Product Name: {product_name}
Product Category: {category_name}
Supplier Name: {supplier_name}

=== SECTIONS TO TITLE ===
{sections_with_ideas}

=== REQUIREMENTS ===
1. Create engaging, SEO-friendly titles for each section
2. Use CLAN product name and terminology when appropriate
3. Titles should be 5-12 words
4. Maintain CLAN''s warm, professional Scottish tone
5. Ensure titles accurately reflect section content

=== OUTPUT FORMAT ===
Return a JSON object:
{{
  "sections": [
    {{
      "section_number": 1,
      "section_name": "Introduction & Historical Context",
      "title": "Engaging title using product name"
    }},
    ...
  ]
}}',
    parameters = '{"model": "llama3.2:latest", "temperature": 0.6, "max_tokens": 1500}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'product_article_section_titling';

-- Product Article Drafting Template (for individual sections)
INSERT INTO llm_prompt (name, description, system_prompt, prompt_text, parameters)
SELECT 
    'product_article_section_drafting',
    'Draft section content for product article with CLAN-first policy',
    'You are a content writer for CLAN.com, a Scottish heritage and culture website. Write engaging, informative blog post sections that prioritize CLAN''s own product data and maintain CLAN''s warm, professional Scottish tone.',
    'You are writing a section for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== CURRENT SECTION ===
Section: {section_name}
Section Title: {section_title}
Section Topics: {section_topics}
Section Ideas: {section_ideas}

=== ALTERNATIVE PRODUCTS (FOR SECTION 6 ONLY) ===
{alternative_products_data}

=== LLM SUPPLEMENTATION RULES ===
1. ALWAYS use CLAN data when available
2. If CLAN data exists but is < 50 words, use it as foundation and expand with LLM knowledge
3. ONLY use LLM knowledge when CLAN data is explicitly missing
4. Mark any LLM-supplemented content with [GENERAL KNOWLEDGE] tag
5. NEVER contradict or override CLAN data

=== REQUIREMENTS ===
1. Write 200-400 words for this section
2. Use CLAN product name exactly as provided
3. Use CLAN supplier information if available
4. Prioritize CLAN heritage data over general knowledge
5. Include specific product details from CLAN data
6. Maintain CLAN''s warm, professional Scottish tone
7. For Alternative Products section: Include 3-5 products with brief descriptions and why they''re alternatives

=== OUTPUT FORMAT ===
Return the section content as plain text (not JSON). Include [GENERAL KNOWLEDGE] tags where LLM supplemented CLAN data.',
    '{"model": "llama3.2:latest", "temperature": 0.7, "max_tokens": 2000}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM llm_prompt WHERE name = 'product_article_section_drafting'
);

UPDATE llm_prompt SET
    description = 'Draft section content for product article with CLAN-first policy',
    system_prompt = 'You are a content writer for CLAN.com, a Scottish heritage and culture website. Write engaging, informative blog post sections that prioritize CLAN''s own product data and maintain CLAN''s warm, professional Scottish tone.',
    prompt_text = 'You are writing a section for a product article on CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
{clan_data_formatted}

=== CURRENT SECTION ===
Section: {section_name}
Section Title: {section_title}
Section Topics: {section_topics}
Section Ideas: {section_ideas}

=== ALTERNATIVE PRODUCTS (FOR SECTION 6 ONLY) ===
{alternative_products_data}

=== LLM SUPPLEMENTATION RULES ===
1. ALWAYS use CLAN data when available
2. If CLAN data exists but is < 50 words, use it as foundation and expand with LLM knowledge
3. ONLY use LLM knowledge when CLAN data is explicitly missing
4. Mark any LLM-supplemented content with [GENERAL KNOWLEDGE] tag
5. NEVER contradict or override CLAN data

=== REQUIREMENTS ===
1. Write 200-400 words for this section
2. Use CLAN product name exactly as provided
3. Use CLAN supplier information if available
4. Prioritize CLAN heritage data over general knowledge
5. Include specific product details from CLAN data
6. Maintain CLAN''s warm, professional Scottish tone
7. For Alternative Products section: Include 3-5 products with brief descriptions and why they''re alternatives

=== OUTPUT FORMAT ===
Return the section content as plain text (not JSON). Include [GENERAL KNOWLEDGE] tags where LLM supplemented CLAN data.',
    parameters = '{"model": "llama3.2:latest", "temperature": 0.7, "max_tokens": 2000}'::jsonb,
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'product_article_section_drafting';
