# Security Fix - Removing Secrets from Git

## ✅ What Was Done

1. ✅ Created `.gitignore` to prevent committing secrets in the future
2. ✅ Removed `.env` files from git tracking
3. ✅ Removed `db.sqlite3` from git tracking (contains access tokens)
4. ✅ Created `env.template` as a safe template file

## ⚠️ Important: Secrets Are Still in Git History

Even though we removed the files, **the secrets are still in your git commit history**. You need to clean the history.

## How to Fix Git History

### Option 1: Use git filter-repo (Recommended)

```bash
# Install git-filter-repo (if not installed)
pip install git-filter-repo

# Remove .env files from all commits
git filter-repo --path .env --invert-paths
git filter-repo --path OJT_project/.env --invert-paths
git filter-repo --path db.sqlite3 --invert-paths

# Force push (WARNING: This rewrites history)
git push origin main --force
```

### Option 2: Use BFG Repo-Cleaner

```bash
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/

# Remove .env files
java -jar bfg.jar --delete-files .env
java -jar bfg.jar --delete-files OJT_project/.env
java -jar bfg.jar --delete-files db.sqlite3

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin main --force
```

### Option 3: Reset and Re-commit (If you haven't pushed yet)

If you haven't pushed to GitHub yet:
```bash
# Reset to before the commit with secrets
git reset --soft HEAD~1

# Remove .env and db.sqlite3
git rm --cached .env OJT_project/.env db.sqlite3

# Re-commit without secrets
git commit -m "Initial commit - OAuth setup without secrets"
```

## After Cleaning History

1. **Regenerate your OAuth credentials** in Google Cloud Console (old ones are compromised)
2. **Update your local `.env` file** with new credentials
3. **Delete old access tokens** from your database

## Next Steps

1. Commit the current changes (removing files):
   ```bash
   git commit -m "Remove sensitive files and add .gitignore"
   ```

2. Clean git history (choose one option above)

3. Force push:
   ```bash
   git push origin main --force
   ```

4. Regenerate OAuth credentials in Google Cloud Console

5. Update your local `.env` file with new credentials

## Prevention

✅ `.gitignore` is now in place - secrets won't be committed again
✅ Use `env.template` as a reference for what variables are needed
✅ Never commit `.env` or `db.sqlite3` files

