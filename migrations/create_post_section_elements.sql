-- Create post_section_elements table
CREATE TABLE post_section_elements (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) NOT NULL,
    section_id INTEGER REFERENCES post_section(id) NOT NULL,
    element_type VARCHAR(50) NOT NULL CHECK (element_type IN ('fact', 'idea', 'theme')),
    element_text TEXT NOT NULL,
    element_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_element_per_section UNIQUE (post_id, section_id, element_text)
);

-- Create indexes for performance
CREATE INDEX idx_post_section_elements_post_id ON post_section_elements(post_id);
CREATE INDEX idx_post_section_elements_section_id ON post_section_elements(section_id);
CREATE INDEX idx_post_section_elements_type ON post_section_elements(element_type);

-- Migrate existing facts from post_development.interesting_facts
WITH fact_array AS (
    SELECT 
        pd.post_id,
        ps.id as section_id,
        unnest(string_to_array(pd.interesting_facts, E'\n')) as element_text,
        row_number() OVER (PARTITION BY pd.post_id, ps.id ORDER BY unnest(string_to_array(pd.interesting_facts, E'\n'))) as element_order
    FROM post_development pd
    JOIN post_section ps ON pd.post_id = ps.post_id
    WHERE pd.interesting_facts IS NOT NULL
)
INSERT INTO post_section_elements (post_id, section_id, element_type, element_text, element_order)
SELECT 
    post_id,
    section_id,
    'fact' as element_type,
    element_text,
    element_order
FROM fact_array
WHERE trim(element_text) <> '';

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_post_section_elements_updated_at
    BEFORE UPDATE ON post_section_elements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 