-- Migration: Create families/clans tables
-- Purpose: Store Scottish family and clan names with relationships and resources
-- Date: 2025-01-XX

BEGIN;

-- Main families table
CREATE TABLE IF NOT EXISTS families (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_clan BOOLEAN DEFAULT FALSE,
    is_virtual BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

-- Indexes for families
CREATE INDEX IF NOT EXISTS idx_families_name ON families(name);
CREATE INDEX IF NOT EXISTS idx_families_is_clan ON families(is_clan);
CREATE INDEX IF NOT EXISTS idx_families_is_virtual ON families(is_virtual);

-- Family aliases (child relationships - alternative names)
CREATE TABLE IF NOT EXISTS family_aliases (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    alias_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(family_id, alias_name)
);

CREATE INDEX IF NOT EXISTS idx_family_aliases_family_id ON family_aliases(family_id);
CREATE INDEX IF NOT EXISTS idx_family_aliases_alias_name ON family_aliases(alias_name);

-- Family spellings (parent relationships - spelling variations)
CREATE TABLE IF NOT EXISTS family_spellings (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    spelling_of_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(family_id, spelling_of_id)
);

CREATE INDEX IF NOT EXISTS idx_family_spellings_family_id ON family_spellings(family_id);
CREATE INDEX IF NOT EXISTS idx_family_spellings_spelling_of_id ON family_spellings(spelling_of_id);

-- Family septs (sub-families of clans)
CREATE TABLE IF NOT EXISTS family_septs (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    sept_of_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(family_id, sept_of_id)
);

CREATE INDEX IF NOT EXISTS idx_family_septs_family_id ON family_septs(family_id);
CREATE INDEX IF NOT EXISTS idx_family_septs_sept_of_id ON family_septs(sept_of_id);

-- Family resources (images, text, JSON data)
CREATE TABLE IF NOT EXISTS family_resources (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- 'image', 'text', 'json', 'location'
    resource_category VARCHAR(255), -- e.g., 'british_fleet', 'scottish_gentry', 'history_legacy'
    resource_value TEXT, -- filename, text content, or JSON string
    resource_metadata JSONB, -- additional structured data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_family_resources_family_id ON family_resources(family_id);
CREATE INDEX IF NOT EXISTS idx_family_resources_type ON family_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_family_resources_category ON family_resources(resource_category);

-- Family designs (links to fabric designs)
CREATE TABLE IF NOT EXISTS family_designs (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    design_id INTEGER, -- ID from external system
    design_year INTEGER, -- Year of design if available
    design_url TEXT, -- URL to design if available
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_family_designs_family_id ON family_designs(family_id);
CREATE INDEX IF NOT EXISTS idx_family_designs_design_id ON family_designs(design_id);

-- Comments
COMMENT ON TABLE families IS 'Scottish family and clan names. is_clan indicates official clans, is_virtual indicates virtual/placeholder entries.';
COMMENT ON TABLE family_aliases IS 'Alternative names for families (child relationships).';
COMMENT ON TABLE family_spellings IS 'Spelling variations linking families to their canonical form (parent relationships).';
COMMENT ON TABLE family_septs IS 'Sept relationships - sub-families that belong to clans.';
COMMENT ON TABLE family_resources IS 'Resources associated with families: images, text content, JSON data, location coordinates.';
COMMENT ON TABLE family_designs IS 'Fabric designs associated with families.';

COMMIT;

