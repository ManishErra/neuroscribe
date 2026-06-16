# Day 35A Database Migration Report

This report documents the database migration executed for Day 35A, including credentials management, schema states, indices, and orphan cleanup tallies.

---

## 1. Schema Upgrades Applied

The database schema was upgraded inside a single transactional block:

*   **Extensions Enabled**: `citext` and `pgcrypto`.
*   **Users Table**: Added `force_password_reset` BOOLEAN column (default `FALSE`).
*   **Patients Table**: Added `owner_id` UUID column referencing `users.id` with `ON DELETE CASCADE` rule to prevent foreign key constraint violations on parent deletions.
*   **Embeddings Table**: Added `owner_id` UUID column referencing `users.id` with `ON DELETE CASCADE`.

---

## 2. Legacy Ownership & Credentials Mapping

All pre-existing clinical records in the database (which were created before multi-user support was introduced) have been backfilled to a secure Legacy System Owner account.

*   **Legacy User ID**: `d35e8400-e29b-41d4-a716-446655440000`
*   **Legacy User Email**: `legacy-owner@neuroscribe.org`
*   **Legacy User Password Hashing**: Hashed using `bcrypt` at runtime with a salt work factor of 12.
*   **Password Security**: 
    - The password was dynamically generated using Python's cryptographically secure random generator: `secrets.token_urlsafe(32)`.
    - Noplaintext passwords or pre-calculated hashes were committed to the repository.
    - Credentials are saved locally in the uncommitted `.env.migration` file inside the workspace root.
    - The legacy user account has been flagged with `force_password_reset = TRUE` to enforce credential rotation upon first login.

---

## 3. Database Orphan Cleanup Tally

Prior to enforcing foreign key constraints, the database was audited and cleared of orphaned records (child records whose parent session or patient had been deleted during past development cycles):

*   **Orphaned Transcripts Deleted**: **0**
*   **Orphaned Notes Deleted**: **0**
*   **Orphaned Reports Deleted**: **0**

---

## 4. Query Performance Indices Created

To prevent query degradation and ensure fast lookups for clinician-specific dashboard displays, the following B-tree indices were created:

1.  `idx_patients_owner_id` on `patients(owner_id)`
2.  `idx_embeddings_owner_id` on `embeddings(owner_id)`
