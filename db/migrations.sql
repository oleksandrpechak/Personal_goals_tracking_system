-- ============================================================================
-- Personal Productivity Tracker — SQL Migrations
-- ============================================================================
-- Run these against your Supabase / PostgreSQL database.
-- They are idempotent (safe to run multiple times).
-- ============================================================================

-- ── Task 3: Performance indexes ─────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_opportunities_created_at
    ON opportunities (created_at);

CREATE INDEX IF NOT EXISTS idx_opportunities_url
    ON opportunities (url);

CREATE INDEX IF NOT EXISTS idx_outreach_targets_status
    ON outreach_targets (status);

-- ── Task 4: Unique constraint for URL deduplication at the DB level ─────────
-- This lets us use INSERT … ON CONFLICT DO NOTHING and removes the need
-- for a separate SELECT-before-INSERT round trip in Python.

ALTER TABLE opportunities
    ADD CONSTRAINT uq_opportunities_url UNIQUE (url);

-- If the above fails because duplicates already exist, deduplicate first:
--
--   DELETE FROM opportunities a USING opportunities b
--   WHERE a.id > b.id AND a.url = b.url;
--
-- Then re-run the ALTER TABLE.

-- ── Task 13: Automatic data cleanup (opportunities older than 180 days) ─────
-- This can be triggered manually or by the scheduler calling
-- OpportunityRepository.cleanup_old().

-- (No DDL needed — the DELETE query lives in db/repository.py.)
-- Manual one-liner if needed:
--
--   DELETE FROM opportunities WHERE created_at < NOW() - INTERVAL '180 days';
