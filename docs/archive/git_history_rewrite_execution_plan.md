# Git History Rewrite Execution Plan

This execution plan outlines the procedure to permanently purge leaked generated passwords from the NeuroScribe repository's commit history (specifically target commit `8335513`) while preserving the working tree.

---

## 1. Required Tools & Prerequisites

We recommend using **`git-filter-repo`** instead of the legacy `git filter-branch`. It is faster, safer, and does not suffer from typical reference loss issues.

### Prerequisites
* **Git**: Git for Windows must be installed.
* **Python**: Python 3.6+ must be installed and added to the Windows environment `PATH`.

---

## 2. Installation Instructions (Windows)

Choose one of the following methods to install `git-filter-repo` on Windows:

### Method A: Via Python Package Manager (Recommended)
1. Open PowerShell or Command Prompt as Administrator.
2. Run the pip installer:
   ```cmd
   pip install git-filter-repo
   ```
3. Verify the installation:
   ```cmd
   git-filter-repo --version
   ```

### Method B: Manual Installation
1. Download the `git-filter-repo` Python script from the [official repository](https://github.com/newren/git-filter-repo/blob/main/git-filter-repo).
2. Save the file to your system.
3. Rename the file to `git-filter-repo` (remove the `.py` extension if present).
4. Copy the script to your Git executables directory, typically:
   `C:\Program Files\Git\mingw64\libexec\git-core\`

---

## 3. Backup Strategy

Before executing any history rewrite, a local and remote backup must be created to support a full rollback:

1. **Create Local Reference Backup**:
   Create a local branch tracking the current pre-rewritten state:
   ```bash
   # Create a backup branch of the active development state
   git branch backup-before-history-cleanup
   ```
2. **Create Mirror Backup (Out of Workspace)**:
   Navigate to the parent directory and perform a full bare clone containing all branches, tags, and commits:
   ```bash
   cd ..
   git clone --mirror https://github.com/ManishErra/neuroscribe.git neuroscribe-backup.git
   ```

---

## 4. Exact Execution Commands

### Step 1: Prepare the Replacement Dictionary
Create a text file named `secrets-to-redact.txt` in the repository root directory containing the text matching rules. The syntax is `text_to_replace==>replacement_text`:

```text
[REDACTED]==>[REDACTED]
[REDACTED]==>[REDACTED]
[REDACTED]==>[REDACTED]
[REDACTED]==>[REDACTED]
```

### Step 2: Run Git-Filter-Repo
Execute the replacement filter. The `--force` flag is required because `git-filter-repo` blocks executions inside active working trees by default:

```bash
git filter-repo --replace-text secrets-to-redact.txt --force
```

*Note: `git-filter-repo` automatically rewrites all commit messages, files, blobs, tags (including the `day35-multi-tenancy` tag), and branches containing these strings.*

### Step 3: Clean Up Leftovers
Delete the dictionary file so it is not accidentally committed:
```bash
rm secrets-to-redact.txt
```

### Step 4: Force Push to Remote Repository
Since history has been modified, git commits will have new hashes. Push the updated states to the public origin:
```bash
# Push all updated branches
git push origin --force --all

# Push all updated tags (such as day35-multi-tenancy)
git push origin --force --tags
```

---

## 5. Verification Steps

To verify that the secrets have been completely removed:

1. **Verify No Secrets Exist in History**:
   Search the entire git history for any of the redacted strings. The output must be completely empty:
   ```bash
   git log -S "[REDACTED]" --oneline
   git log -S "[REDACTED]" --oneline
   ```
2. **Verify Redacted Markers Exist**:
   Verify that the report files now contain the `[REDACTED]` string in historical commit logs:
   ```bash
   git log -S "[REDACTED]" --oneline
   ```

---

## 6. Rollback Steps

If any references are corrupted or if the history rewrite causes errors:

### Rollback Local Repository
Reset the branch back to the pre-cleanup local backup:
```bash
git reset --hard backup-before-history-cleanup
```

### Restore Remote Origin (If Force Pushed)
If the remote repository was updated before discovering the error, restore all branches and tags from the bare mirror clone backup:
```bash
cd ../neuroscribe-backup.git
git push origin --force --all
git push origin --force --tags
```
