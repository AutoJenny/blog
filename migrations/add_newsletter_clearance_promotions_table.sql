-- Migration: Create newsletter_clearance_promotions table
-- Purpose: Track which clearance products have been promoted in newsletters
-- Date: 2025-11-26

BEGIN;

CREATE TABLE IF NOT EXISTS newsletter_clearance_promotions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    product_url TEXT NOT NULL,
    product_title TEXT NOT NULL,
    image_url TEXT NOT NULL,
    price_now NUMERIC(10,2) NOT NULL,
    price_was NUMERIC(10,2) NOT NULL,
    discount_percentage NUMERIC(5,2) NOT NULL,
    specifications JSONB NOT NULL DEFAULT '{}',
    category_branch_id INTEGER REFERENCES clan_categories(id),
    category_leaf_id INTEGER REFERENCES clan_categories(id),
    issue_id INTEGER REFERENCES newsletter_issue(id),
    block_id INTEGER REFERENCES newsletter_block(id),
    promoted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clearance_promotions_product_id ON newsletter_clearance_promotions(product_id);
CREATE INDEX IF NOT EXISTS idx_clearance_promotions_issue_id ON newsletter_clearance_promotions(issue_id);
CREATE INDEX IF NOT EXISTS idx_clearance_promotions_block_id ON newsletter_clearance_promotions(block_id);
CREATE INDEX IF NOT EXISTS idx_clearance_promotions_category_branch ON newsletter_clearance_promotions(category_branch_id);
CREATE INDEX IF NOT EXISTS idx_clearance_promotions_promoted_at ON newsletter_clearance_promotions(promoted_at);

COMMENT ON TABLE newsletter_clearance_promotions IS 'Tracks clearance products that have been promoted in newsletter last_chance blocks';
COMMENT ON COLUMN newsletter_clearance_promotions.product_id IS 'Product ID from clan_products (if exists) or extracted from URL';
COMMENT ON COLUMN newsletter_clearance_promotions.category_branch_id IS 'Branch category (parent of leaf) to ensure diversity';
COMMENT ON COLUMN newsletter_clearance_promotions.category_leaf_id IS 'Leaf category (deepest category) for the product';

COMMIT;

