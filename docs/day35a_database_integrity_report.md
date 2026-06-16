# Day 35A Database Integrity Audit Report

This report documents the Day 35A Database Integrity Audit executed prior to starting Day 35B. It inspects the PostgreSQL schema, indexes, ownership backfills, legacy owner status, and orphaned records on the Supabase PostgreSQL database.

---

## 1. SQL Queries Executed & Outputs

### A. PostgreSQL Schema Inspection
*   **Verification Objective**: Confirm that `patients.owner_id`, `embeddings.owner_id`, and `users.force_password_reset` exist and have correct schemas.
*   **SQL Queries Executed**:
    ```sql
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name='patients' AND column_name='owner_id';
    
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name='embeddings' AND column_name='owner_id';
    
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name='users' AND column_name='force_password_reset';
    ```
*   **Query Output**:
    ```text
    Table: patients   | Column: owner_id             | Type: uuid    | Nullable: NO  -> PASS
    Table: embeddings | Column: owner_id             | Type: uuid    | Nullable: NO  -> PASS
    Table: users      | Column: force_password_reset | Type: boolean | Nullable: NO  -> PASS
    ```
*   **Status**: **PASS**

---

### B. PostgreSQL Index Inspection
*   **Verification Objective**: Confirm that indexes `idx_patients_owner_id` and `idx_embeddings_owner_id` exist.
*   **SQL Queries Executed**:
    ```sql
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename='patients' AND indexname='idx_patients_owner_id';
    
    SELECT indexname, indexdef 
    FROM pg_indexes 
    WHERE tablename='embeddings' AND indexname='idx_embeddings_owner_id';
    ```
*   **Query Output**:
    ```text
    Index: idx_patients_owner_id   | Definition: CREATE INDEX idx_patients_owner_id ON public.patients USING btree (owner_id)   -> PASS
    Index: idx_embeddings_owner_id | Definition: CREATE INDEX idx_embeddings_owner_id ON public.embeddings USING btree (owner_id) -> PASS
    ```
*   **Status**: **PASS**

---

### C. Ownership Backfill Verification
*   **Verification Objective**: Count NULL owner_ids and verify distributions.
*   **SQL Queries Executed**:
    ```sql
    SELECT COUNT(*) FROM patients WHERE owner_id IS NULL;
    
    SELECT COUNT(*) FROM embeddings WHERE owner_id IS NULL;
    
    SELECT owner_id, COUNT(*) FROM patients GROUP BY owner_id;
    
    SELECT owner_id, COUNT(*) FROM embeddings GROUP BY owner_id;
    ```
*   **Query Output**:
    ```text
    Patients with NULL owner_id: 0 -> PASS
    Embeddings with NULL owner_id: 0 -> PASS
    
    Distribution of owner_id across patients:
      - owner_id: d35e8400-e29b-41d4-a716-446655440000 | Count: 6
      
    Distribution of owner_id across embeddings:
      - owner_id: d35e8400-e29b-41d4-a716-446655440000 | Count: 6
    ```
*   **Status**: **PASS** (100% of existing patients and embeddings are securely mapped to the Legacy System Owner).

---

### D. Legacy Owner Verification
*   **Verification Objective**: Confirm the legacy user exists, is flagged for reset, and credentials are protected.
*   **SQL Query Executed** (excluding password hash):
    ```sql
    SELECT id, email, name, force_password_reset 
    FROM users 
    WHERE id = 'd35e8400-e29b-41d4-a716-446655440000';
    ```
*   **Query Output**:
    ```text
    ID: d35e8400-e29b-41d4-a716-446655440000
    Email: legacy-owner@neuroscribe.org
    Name: Legacy System Owner
    force_password_reset: True -> PASS
    ```
*   **Status**: **PASS**

---

### E. Orphan Verification
*   **Verification Objective**: Count transcripts and notes with NULL `session_id` and check if they still exist.
*   **SQL Queries Executed**:
    ```sql
    SELECT COUNT(*) FROM transcripts WHERE session_id IS NULL;
    
    SELECT COUNT(*) FROM notes WHERE session_id IS NULL;
    ```
*   **Query Output**:
    ```text
    Transcripts where session_id IS NULL: 12
    Notes where session_id IS NULL: 8
    ```
*   **Confirmation**: **YES, these records still exist after Day 35A.** 
*   **Root Cause**: The migration script `apply_day35_migration.py` executed `DELETE FROM transcripts WHERE session_id NOT IN (SELECT id FROM sessions)`. In SQL, `NULL NOT IN (list)` evaluates to `UNKNOWN`, meaning rows where `session_id IS NULL` are NOT matched and NOT deleted by the query.
*   **Status**: **FAIL** (Orphan records were not cleaned up due to the SQL `NOT IN` logic error).

---

## 2. Verification Summary Table

| Check Item | SQL Verification Query | Expected State | Actual State | Status |
| :--- | :--- | :--- | :--- | :---: |
| **patients.owner_id** | `information_schema.columns` check | Exists (UUID, NOT NULL) | Exists (UUID, NOT NULL) | **PASS** |
| **embeddings.owner_id** | `information_schema.columns` check | Exists (UUID, NOT NULL) | Exists (UUID, NOT NULL) | **PASS** |
| **users.force_password_reset** | `information_schema.columns` check | Exists (BOOLEAN, NOT NULL) | Exists (BOOLEAN, NOT NULL) | **PASS** |
| **idx_patients_owner_id** | `pg_indexes` check | Exists | Exists | **PASS** |
| **idx_embeddings_owner_id** | `pg_indexes` check | Exists | Exists | **PASS** |
| **Backfilled Patients** | `owner_id IS NULL` check | `0` | `0` | **PASS** |
| **Backfilled Embeddings** | `owner_id IS NULL` check | `0` | `0` | **PASS** |
| **Legacy User Row** | `users` query by ID | Exists, `force_password_reset=TRUE` | Exists, `force_password_reset=True` | **PASS** |
| **Orphan Transcripts** | `session_id IS NULL` check | `0` | `12` | **FAIL** |
| **Orphan Notes** | `session_id IS NULL` check | `0` | `8` | **FAIL** |

---

## 3. Final Conclusion

### **Day35A Requires Fixes Before Day35B**

**Justification**:
While the schema, indexes, legacy owner record, and ownership backfills are 100% correct, the **database orphan cleanup failed**. There are still **12 orphaned transcripts** and **8 orphaned notes** residing in the database. 

This must be corrected before proceeding to Day 35B.

**Required Fixes**:
The orphan deletion statements in `apply_day35_migration.py` must be corrected to:
```python
conn.execute(text("DELETE FROM transcripts WHERE session_id IS NULL OR session_id NOT IN (SELECT id FROM sessions)"))
conn.execute(text("DELETE FROM notes WHERE session_id IS NULL OR session_id NOT IN (SELECT id FROM sessions)"))
```
Once the migration script is fixed, a rollback, a re-run of the migration, and verification must be performed to confirm that the orphans are deleted (counts return 0) before Day 35B can begin.
