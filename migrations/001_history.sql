CREATE SCHEMA IF NOT EXISTS profit_private;
REVOKE ALL ON SCHEMA profit_private FROM PUBLIC, anon, authenticated;
CREATE TABLE IF NOT EXISTS profit_private.calculation_history (
    sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_hash text NOT NULL,
    event_id text NOT NULL,
    record jsonb NOT NULL,
    UNIQUE (owner_hash, event_id)
);
CREATE INDEX IF NOT EXISTS calculation_history_owner_sequence
ON profit_private.calculation_history (owner_hash, sequence DESC);
ALTER TABLE profit_private.calculation_history ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON profit_private.calculation_history FROM PUBLIC, anon, authenticated;
