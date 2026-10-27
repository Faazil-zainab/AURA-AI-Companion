-- Phase 1 verifies that the local SQLite connection can be initialized.
-- Conversation and memory tables are added in Phase 3.
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_metadata (key, value)
VALUES ('schema_version', '1');
