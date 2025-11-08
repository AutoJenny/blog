-- Migration: Create producers table
-- Purpose: Normalize producer/supplier information for Product Profiles
-- Date: 2025-01-XX

BEGIN;

-- Create producers table
CREATE TABLE IF NOT EXISTS producers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    location VARCHAR(255),
    founding_year INTEGER,
    heritage_details TEXT,
    craftsmanship_methods TEXT,
    website_url VARCHAR(500),
    web_researched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_producers_name ON producers(name);

-- Add comment to table
COMMENT ON TABLE producers IS 'Normalized producer/supplier information for Product Profiles. Populated from clan_products.supplier_name and enriched via web research.';

COMMIT;




