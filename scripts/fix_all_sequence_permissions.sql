-- Fix all sequence permissions and ownership for blog project
-- Grants USAGE, SELECT, UPDATE to both nickfiddes and postgres
-- Sets owner to nickfiddes for all sequences

DO $$
DECLARE
    seq RECORD;
BEGIN
    FOR seq IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public' LOOP
        EXECUTE format('GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.%I TO nickfiddes;', seq.sequence_name);
        EXECUTE format('GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.%I TO postgres;', seq.sequence_name);
        EXECUTE format('ALTER SEQUENCE public.%I OWNER TO nickfiddes;', seq.sequence_name);
    END LOOP;
END $$; 