# Fix Redirect URI Mismatch Error

## The Problem
Google is rejecting the OAuth request because the redirect URI doesn't match what's configured in Google Cloud Console.

## Solution Steps

### Step 1: Check What Redirect URI Django is Using

The redirect URI should be one of these:
- `http://localhost:8000/auth/google/callback/`
- `http://127.0.0.1:8000/auth/google/callback/`

### Step 2: Update Google Cloud Console

1. Go to: **https://console.cloud.google.com/apis/credentials**
2. Find your OAuth 2.0 Client ID (the one you created earlier)
3. Click the **Edit** (pencil) icon
4. In the **"Authorized redirect URIs"** section:
   - **Remove** any existing redirect URIs
   - **Add BOTH** of these (click "+ Add URI" for each):
     - `http://localhost:8000/auth/google/callback/`
     - `http://127.0.0.1:8000/auth/google/callback/`
5. Click **"Save"** at the bottom
6. Wait 1-2 minutes for changes to propagate

### Step 3: Important Notes

- The redirect URI must match **EXACTLY** including:
  - `http://` (not `https://`)
  - `localhost` or `127.0.0.1` (both should be added)
  - Port number `:8000`
  - The path `/auth/google/callback/`
  - **Trailing slash** `/` at the end

### Step 4: Test Again

1. Restart your Django server
2. Go to `http://localhost:8000/login/`
3. Click "Continue with Google"
4. It should now work!

## Common Mistakes

❌ **Wrong:** `http://localhost:8000/auth/google/callback` (missing trailing slash)
❌ **Wrong:** `https://localhost:8000/auth/google/callback/` (using https)
❌ **Wrong:** `http://localhost/auth/google/callback/` (missing port)
✅ **Correct:** `http://localhost:8000/auth/google/callback/`

