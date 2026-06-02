# Migration Hardening Report

This report outlines the technical plan for migrating the existing single-clinician database schema to the User-Patient Ownership Model. It details transactional DDL, backfill strategies for legacy records, credential security safeguards, and the FAISS vector store metadata migration path.

---

## 1. Legacy Ownership Strategy & Credential Security

The database currently contains:
*   4 patients
*   17 sessions
*   21 transcripts
*   19 notes
*   38 reports
*   6 embeddings
*   0 users

To enforce foreign key constraints, we must map these existing clinical records to a "Legacy System Owner" account.

### Security Constraints:
*   **No Plaintext Passwords**: No default passwords (e.g. "Admin@123") may be committed to version control or documented in text.
*   **No Committed Hashes**: No pre-calculated bcrypt hashes derived from known passwords may be hardcoded in migration scripts.

### Proposed Secure Approach:
1.  **On-Demand Runtime Generation**: During the migration script execution, the script will generate a cryptographically secure, random 32-character password using Python's standard `secrets` module:
    ```python
    import secrets
    raw_password = secrets.token_urlsafe(32)
    ```
2.  **Bcrypt Hashing at Runtime**: The script will hash the generated password at runtime using `bcrypt` and write the hash to the `users` table:
    ```python
    import bcrypt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')
    ```
3.  **Forced Password Reset Flag**: The migration script will insert the legacy user and set a boolean flag `force_password_reset = TRUE` in their database row (or custom settings metadata).
4.  **Logging**: The script will print the generated password **only once** to the standard output console or a temporary secure migration log, prompting the administrator to save it securely or reset it immediately.

---

## 2. Database Migration SQL Script (Supabase-Compatible)

The migration will be applied inside a transaction to ensure that any failure triggers an automatic rollback, preventing partial or corrupted schemas.

```sql
-- Day 35 Database Migration SQL Script
BEGIN;

-- 1. Ensure required extensions are available
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Create the legacy system owner user first
-- The hashed_password below is generated at runtime by the python migration wrapper.
-- We insert a placeholder row that will be updated with the securely generated hash.
INSERT INTO users (id, email, hashed_password, name, created_at)
VALUES (
    'd35e8400-e29b-41d4-a716-446655440000', -- Deterministic UUID for legacy owner
    'legacy-owner@neuroscribe.org',
    '$2b$12$DUMMYHASHFORSAFETYEXCLUSIONONLY...', -- Replaced dynamically at runtime
    'Legacy System Owner',
    NOW()
);

-- Add force_password_reset column to users if not present to enforce reset
ALTER TABLE users ADD COLUMN IF NOT EXISTS force_password_reset BOOLEAN NOT NULL DEFAULT FALSE;
UPDATE users SET force_password_reset = TRUE WHERE id = 'd35e8400-e29b-41d4-a716-446655440000';

-- 3. Migrate patients table
-- Step A: Add owner_id as nullable initially
ALTER TABLE patients ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- Step B: Backfill existing records to legacy owner
UPDATE patients SET owner_id = 'd35e8400-e29b-41d4-a716-446655440000' WHERE owner_id IS NULL;

-- Step C: Alter column to NOT NULL
ALTER TABLE patients ALTER COLUMN owner_id SET NOT NULL;

-- 4. Migrate database embeddings table
-- Step A: Add owner_id as nullable
ALTER TABLE embeddings ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Step B: Backfill database embeddings by joining notes or reports
-- Note source backfill
UPDATE embeddings e
SET owner_id = p.owner_id
FROM notes n
JOIN sessions s ON n.session_id = s.id
JOIN patients p ON s.patient_id = p.id
WHERE e.source_type = 'note' AND e.source_id = n.id;

-- Report source backfill
UPDATE embeddings e
SET owner_id = p.owner_id
FROM reports r
JOIN patients p ON r.patient_id = p.id
WHERE e.source_type = 'report' AND e.source_id = r.id;

-- Fallback for orphaned embeddings (should be 0 rows)
UPDATE embeddings SET owner_id = 'd35e8400-e29b-41d4-a716-446655440000' WHERE owner_id IS NULL;

-- Step C: Alter column to NOT NULL
ALTER TABLE embeddings ALTER COLUMN owner_id SET NOT NULL;

-- 5. Create performance indexes for scoped queries
CREATE INDEX IF NOT EXISTS idx_patients_owner_id ON patients(owner_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_owner_id ON embeddings(owner_id);

COMMIT;
```

---

## 3. FAISS Metadata Migration Strategy

The local reports vector store utilizes an on-disk FAISS index (`vector.index`) and a metadata file (`vector_metadata.json`) containing report segment mappings.

### Whether `owner_id` is added to metadata:
**Yes.** We will inject the `owner_id` field into each chunk's dictionary inside the metadata file. This avoids executing high-latency SQL lookups for every candidate chunk returned during vector search.

### Whether reindexing is required:
**No.** The float vector embeddings stored inside the binary `vector.index` are mathematical representations of the text chunks and do not contain ownership information. They do not need to be recalculated or reindexed, which saves significant computing resources and avoids paid model call dependencies.

### Whether metadata can be patched without recomputing embeddings:
**Yes.** The `vector_metadata.json` file can be patched dynamically using a Python migration utility script. The script performs the following:
1.  Connects to the database and builds a lookup mapping of `report_id -> owner_id` (by joining `reports` with `patients`).
2.  Reads the existing `vector_metadata.json` file.
3.  Loops through each metadata chunk, looks up the corresponding `report_id` in the database mapping, and injects the `"owner_id": "<UUID>"` key-value pair.
4.  Writes the updated list back to `vector_metadata.json` atomically.

### Expected Downtime:
*   **SQL Schema Alteration**: < 50 milliseconds (since the database tables are small, adding columns and constraints is extremely fast).
*   **FAISS Metadata Patching**: < 10 milliseconds.
*   **Total Expected Downtime**: **Zero Downtime**. The JSON update is applied atomically via a file replace, and the database script runs in a single fast transaction.

### Migration Risks:
1.  **Index/Metadata Length Mismatch**: FAISS requires that the total vectors in `vector.index` (`loaded_index.ntotal`) matches the length of the list in `vector_metadata.json` exactly. If reports are uploaded or deleted during the migration, the sizes could drift, causing FAISS to raise index size mismatches on boot.
    *   *Mitigation*: Run the migration during a quiet window and lock the reports upload router during execution.
2.  **Orphaned Metadata Chunks**: If there are chunks in `vector_metadata.json` pointing to a `report_id` that has already been deleted from the PostgreSQL database, the owner lookup will fail.
    *   *Mitigation*: The patching script will assign any unresolved `report_id` to the default `d35e8400-e29b-41d4-a716-446655440000` legacy owner account instead of crashing.
3.  **Concurrency / Lock Contention**: While altering tables to add foreign keys, PostgreSQL acquires an `ACCESS EXCLUSIVE` lock on the tables (`patients` and `embeddings`), blocking all reads and writes.
    *   *Mitigation*: Ensure the statement timeout is set, and execute the migration when there are no active clinical sessions.

---

## 4. Concurrency and Lock Contention Safeguards

To prevent lock queuing and timeouts in production:
*   **Statement Timeout**: Enforce `SET local lock_timeout = '2s';` before the transaction to prevent the migration from blocking other queries if an exclusive lock cannot be acquired immediately.
*   **Concurrent Indexing**: For larger databases, create indexes concurrently (outside of transactions) before applying constraints to keep lock durations minimal.
