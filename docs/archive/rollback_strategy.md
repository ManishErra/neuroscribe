# Rollback Strategy

This document details the recovery and schema reversion procedures in the event of database migration failures, data corruption, or application regressions during the Day 35 User-Patient Ownership Model deployment.

---

## 1. Database Schema Reversion SQL Script

If a migration fails or must be rolled back to restore the Day 34 schema structure, run the following SQL script in the Supabase SQL editor or migration runner:

```sql
-- Revert Day 35 Migration Schema Upgrades
BEGIN;

-- 1. Drop indexes created for owner isolation
DROP INDEX IF EXISTS idx_patients_owner_id;
DROP INDEX IF EXISTS idx_embeddings_owner_id;

-- 2. Drop owner_id constraint and column from embeddings
ALTER TABLE embeddings DROP CONSTRAINT IF EXISTS embeddings_owner_id_fkey;
ALTER TABLE embeddings DROP COLUMN IF EXISTS owner_id;

-- 3. Drop owner_id constraint and column from patients
ALTER TABLE patients DROP CONSTRAINT IF EXISTS patients_owner_id_fkey;
ALTER TABLE patients DROP COLUMN IF EXISTS owner_id;

-- 4. Clean up the default force_password_reset column from users if it was added
ALTER TABLE users DROP COLUMN IF EXISTS force_password_reset;

-- 5. Delete the legacy system owner user account
DELETE FROM users WHERE id = 'd35e8400-e29b-41d4-a716-446655440000';

COMMIT;
```

---

## 2. FAISS Vector Store Metadata Reversion

To revert the `vector_metadata.json` updates and restore it to its Day 34 state:
1.  **Discard owner_id fields**: Run the metadata restore script to strip out all `"owner_id"` keys from the JSON metadata elements.
    ```python
    import json
    from pathlib import Path

    metadata_file = Path("backend/vector_metadata.json")
    if metadata_file.is_file():
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Remove owner_id key from all elements
        for item in data:
            item.pop("owner_id", None)
            
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("FAISS metadata owner_id fields stripped successfully.")
    ```
2.  **Verify size consistency**: Check that `vector_metadata.json` length matches the `vector.index` `ntotal` vectors count exactly.

---

## 3. Application Code Down-Level Checklist

If backend server execution fails post-deployment, perform the following steps to roll back application code:
1.  **Stash or Discard Local Changes**:
    ```bash
    git reset --hard HEAD
    ```
2.  **Checkout Day 34 Codebase Baseline**:
    Checkout the Day 34 tag or stable commit:
    ```bash
    git checkout 945b1e9
    ```
3.  **Restore Environment Variables**: Remove any new variables added in `.env` or `.env.local` related to Day 35 settings if they conflict.
4.  **Re-run Backend Unit Verification**: Execute the Day 34 verification script to ensure all public/private routes are operational:
    ```bash
    .venv/Scripts/python backend/scripts/run_day34_verification.py
    ```

---

## 4. Post-Rollback Data Health Verification Checks

Run the following SQL queries post-reversion to confirm that the database is healthy and no patient or session records were lost or orphaned during rollback:

*   **Check Row Count Integrity**:
    ```sql
    SELECT COUNT(*) FROM patients;      -- Expected: Matches pre-migration row count (e.g. 4)
    SELECT COUNT(*) FROM sessions;      -- Expected: Matches pre-migration row count (e.g. 17)
    SELECT COUNT(*) FROM notes;         -- Expected: Matches pre-migration row count (e.g. 19)
    SELECT COUNT(*) FROM reports;       -- Expected: Matches pre-migration row count (e.g. 38)
    SELECT COUNT(*) FROM embeddings;    -- Expected: Matches pre-migration row count (e.g. 6)
    ```
*   **Check for Orphaned Sessions**:
    ```sql
    SELECT COUNT(*) FROM sessions s LEFT JOIN patients p ON s.patient_id = p.id WHERE p.id IS NULL; -- Expected: 0
    ```
*   **Check for Missing Columns**:
    Confirm that `owner_id` has been successfully removed from `patients` and `embeddings` schemas.
