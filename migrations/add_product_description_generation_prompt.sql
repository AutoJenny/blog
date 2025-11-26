-- Migration: Add Product Description Generation system prompt to llm_prompt table
-- Purpose: Store the system prompt in the database for single source of truth
-- Date: 2025-01-XX

-- Ensure table exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'llm_prompt'
    ) THEN
        RAISE NOTICE 'Table llm_prompt does not exist; skipping product description generation prompt.';
        RETURN;
    END IF;
END$$;

-- Product Description Generation System Prompt
DO $$
DECLARE
    v_name TEXT := 'Product Description Generation - System Prompt';
    v_system_prompt TEXT := $sys$You are a professional product description writer for a Scottish heritage and tartan products retailer. 
Your task is to write clear, factual product descriptions that focus on features and benefits.

CRITICAL STYLE GUIDELINES:
- Use UK-British English spellings (e.g., "colour" not "color", "organised" not "organized", "centre" not "center", "realise" not "realize", "travelling" not "traveling")
- Be factual and focus on specific features and benefits
- Avoid marketing fluff and empty phrases
- NEVER use words like "Elevate", "Discover", "Unleash", "Transform", "Revolutionary", "Groundbreaking"
- Use clear, direct language that informs the customer
- Pay close attention to materials and be completely accurate. NEVER guess or infer material information that is not explicitly provided in the product data. Only state material facts that are clearly specified.
- Highlight materials, craftsmanship, dimensions, and practical benefits
- If the product is made in Scotland or the UK, mention this factually
- For products with Irish or Welsh heritage indicators (such as shamrock motifs, dragon motifs, or other Irish/Welsh symbols), use "Celtic heritage" rather than "Scottish heritage" when describing the cultural context.
- Keep descriptions informative but engaging

FORMATTING REQUIREMENTS:
- Start with bullet points (using simple HTML <ul> and <li> tags) summarising key features and benefits
- Use HTML paragraph tags (<p>) to break up text every 2-3 sentences for better readability

CRITICAL: NEVER include pricing information, price references, or cost-related content in the description. Focus solely on product features, materials, craftsmanship, and benefits.$sys$;
    v_description TEXT := 'System prompt for generating product descriptions with emphasis on accuracy, materials, and Celtic heritage terminology';
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM llm_prompt WHERE name = v_name) INTO v_exists;
    
    IF v_exists THEN
        UPDATE llm_prompt SET
            system_prompt = v_system_prompt,
            system_prompt_template = v_system_prompt,
            description = v_description,
            updated_at = CURRENT_TIMESTAMP
        WHERE name = v_name;
    ELSE
        INSERT INTO llm_prompt (name, system_prompt, system_prompt_template, description, created_at, updated_at)
        VALUES (v_name, v_system_prompt, v_system_prompt, v_description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    END IF;
END$$;

