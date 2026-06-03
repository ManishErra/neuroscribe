import sys
import os
import subprocess
from pathlib import Path
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import SessionLocal

def run_git_release_audit():
    print("=== STARTING DAY 35 GIT RELEASE AUDIT ===")
    
    backend_dir = Path(__file__).resolve().parent.parent
    root_dir = backend_dir.parent
    
    audit_passed = True
    
    # ----------------------------------------------------
    # 1. Repository Hygiene & Git Status Audit
    # ----------------------------------------------------
    print("\n--- 1. Git Status Audit ---")
    try:
        # Run git status --porcelain
        res = subprocess.run(["git", "status", "--porcelain"], cwd=str(root_dir), capture_output=True, text=True, check=True)
        git_lines = res.stdout.strip().split("\n")
        
        modified_files = []
        untracked_files = []
        
        for line in git_lines:
            if not line:
                continue
            status = line[:2].strip()
            filepath = line[3:].strip()
            
            if status in ("M", "AM", "MM"):
                modified_files.append(filepath)
            elif status == "??":
                untracked_files.append(filepath)
                
        print(f"  Modified files pending commit ({len(modified_files)}):")
        for f in modified_files:
            print(f"    - {f}")
            
        print(f"  Untracked files ({len(untracked_files)}):")
        for f in untracked_files:
            print(f"    - {f}")
            
    except Exception as e:
        print(f"  FAIL: Failed to run git status: {e}")
        sys.exit(1)
        
    # ----------------------------------------------------
    # 2. Sensitive Data Audit
    # ----------------------------------------------------
    print("\n--- 2. Sensitive Data Audit ---")
    sensitive_patterns = [
        ".env",
        ".env.migration",
        "vector_metadata.backup.json"
    ]
    
    staged_sensitive = []
    
    # Check if any sensitive patterns are tracked or about to be committed
    try:
        res_staged = subprocess.run(["git", "diff", "--name-only", "--cached"], cwd=str(root_dir), capture_output=True, text=True, check=True)
        staged_files = res_staged.stdout.strip().split("\n")
        for f in staged_files:
            if not f:
                continue
            for pattern in sensitive_patterns:
                if pattern in f:
                    staged_sensitive.append(f)
    except Exception as e:
        print(f"  FAIL: Failed to check staged files: {e}")
        sys.exit(1)
        
    # Double check that we have ignore configured for env files
    try:
        for f_check in [".env", ".env.migration"]:
            check_res = subprocess.run(["git", "check-ignore", f_check], cwd=str(root_dir), capture_output=True, text=True)
            ignored = (check_res.returncode == 0)
            print(f"  Git ignores '{f_check}'                         : {'YES' if ignored else 'NO'}")
            if not ignored:
                print(f"    FAIL: '{f_check}' is not protected by gitignore.")
                audit_passed = False
    except Exception as e:
        print(f"  FAIL: Failed to run git check-ignore: {e}")
        sys.exit(1)
        
    # Verify backup metadata file is not staged
    backup_path = backend_dir / "vector_metadata.backup.json"
    backup_exists = backup_path.is_file()
    print(f"  vector_metadata.backup.json exists on disk  : {'YES' if backup_exists else 'NO'}")
    
    # Check if it is tracked or staged
    try:
        check_backup = subprocess.run(["git", "ls-files", "backend/vector_metadata.backup.json"], cwd=str(root_dir), capture_output=True, text=True)
        tracked = len(check_backup.stdout.strip()) > 0
        print(f"  vector_metadata.backup.json is tracked by git: {'YES' if tracked else 'NO'}")
        if tracked:
            print("    FAIL: backup metadata file is tracked; must not be committed.")
            audit_passed = False
    except Exception as e:
        print(f"  FAIL: ls-files check failed: {e}")
        sys.exit(1)
        
    if staged_sensitive:
        print("  FAIL: Sensitive files staged for commit:")
        for f in staged_sensitive:
            print(f"    - {f}")
        audit_passed = False
    else:
        print("  PASS: No sensitive credentials or backup metadata files staged.")
        
    # ----------------------------------------------------
    # 3. Database Cleanup Audit
    # ----------------------------------------------------
    print("\n--- 3. Database Cleanup Audit ---")
    db = SessionLocal()
    try:
        # Check for temporary Doctor A / Doctor B accounts
        query_doctors = "SELECT COUNT(*) FROM users WHERE email LIKE 'doctor-a-%' OR email LIKE 'doctor-b-%'"
        doctor_count = db.execute(text(query_doctors)).scalar()
        print(f"  Temporary doctor accounts in DB             : {doctor_count}")
        
        # Check for temporary patients
        query_patients = "SELECT COUNT(*) FROM patients WHERE name LIKE 'Patient Owned By A' OR name LIKE 'Patient C' OR name LIKE 'Audit Patient C'"
        patient_count = db.execute(text(query_patients)).scalar()
        print(f"  Temporary test patients in DB               : {patient_count}")
        
        # Check for temporary reports
        # (Since patient is cascade deleted, temporary reports should also be 0)
        query_reports = """
            SELECT COUNT(*) FROM reports r 
            LEFT JOIN patients p ON r.patient_id = p.id 
            WHERE p.id IS NULL AND r.ocr_text LIKE '%Audit Patient C%'
        """
        report_count = db.execute(text(query_reports)).scalar()
        print(f"  Orphaned/temporary reports in DB            : {report_count}")
        
        db_cleanup_ok = (doctor_count == 0 and patient_count == 0 and report_count == 0)
        print(f"  All temporary verification DB rows purged    : {'PASS' if db_cleanup_ok else 'FAIL'}")
        if not db_cleanup_ok:
            audit_passed = False
            
    except Exception as e:
        print(f"  FAIL: Database cleanup check failed: {e}")
        db.close()
        sys.exit(1)
    db.close()
    
    # ----------------------------------------------------
    # 4. Final Classification
    # ----------------------------------------------------
    print("\n--- 4. Release Recommendation ---")
    if audit_passed:
        print("RELEASE AUDIT CLASSIFICATION: APPROVED FOR GIT COMMIT")
        sys.exit(0)
    else:
        print("RELEASE AUDIT CLASSIFICATION: REJECTED")
        sys.exit(1)

if __name__ == "__main__":
    run_git_release_audit()
