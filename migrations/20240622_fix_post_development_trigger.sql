-- Drop the existing trigger
DROP TRIGGER IF EXISTS update_post_development_updated_at ON post_development;

-- Drop the existing function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Create the function with a different name to avoid conflicts
CREATE OR REPLACE FUNCTION update_post_development_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create the trigger with the new function
CREATE TRIGGER update_post_development_updated_at
    BEFORE UPDATE ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION update_post_development_updated_at_column(); 