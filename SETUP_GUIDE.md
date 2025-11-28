# Google OAuth Setup Guide - Step by Step

This guide will walk you through setting up Google OAuth2 credentials for your Calendar Sync project.

---

## Step 1: Create the .env File

1. Navigate to your project folder: `OJT_project/`
2. Create a new file named `.env` (no extension, just `.env`)
3. Open the `.env` file in a text editor
4. Add these lines (we'll fill in the values later):

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

**Note:** Keep this file secure and never commit it to Git!

---

## Step 2: Go to Google Cloud Console

1. Open your web browser
2. Go to: **https://console.cloud.google.com/**
3. Sign in with your Google account (the one you want to use for testing)

---

## Step 3: Create or Select a Project

### Option A: Create a New Project
1. Click the project dropdown at the top (next to "Google Cloud")
2. Click **"New Project"**
3. Enter a project name: `Calendar Sync App` (or any name you prefer)
4. Click **"Create"**
5. Wait a few seconds for the project to be created
6. Select your new project from the dropdown

### Option B: Use Existing Project
1. Click the project dropdown at the top
2. Select your existing project from the list

---

## Step 4: Enable Google Calendar API

1. In the left sidebar, click **"APIs & Services"** → **"Library"**
   - (Or go directly to: https://console.cloud.google.com/apis/library)
2. In the search bar at the top, type: **"Google Calendar API"**
3. Click on **"Google Calendar API"** from the results
4. Click the blue **"Enable"** button
5. Wait a few seconds for it to enable
6. You should see a green checkmark and "API enabled" message

---

## Step 5: Configure OAuth Consent Screen

1. In the left sidebar, click **"APIs & Services"** → **"OAuth consent screen"**
2. You'll see a form to configure your app:
   - **User Type:** Select **"External"** (unless you have a Google Workspace account)
   - Click **"Create"**
3. Fill in the **App information:**
   - **App name:** `Calendar Sync Hub` (or any name)
   - **User support email:** Select your email
   - **App logo:** (Optional - skip for now)
   - **Application home page:** `http://localhost:8000`
   - **Authorized domains:** (Leave empty for localhost)
   - **Developer contact information:** Your email
4. Click **"Save and Continue"**
5. On the **Scopes** page:
   - Click **"Add or Remove Scopes"**
   - In the filter box, type: `calendar`
   - Check the box: **`.../auth/calendar`** (Google Calendar API)
   - Click **"Update"**
   - Click **"Save and Continue"**
6. On the **Test users** page (if you selected External):
   - Click **"Add Users"**
   - Add your Google email address
   - Click **"Add"**
   - Click **"Save and Continue"**
7. Review and click **"Back to Dashboard"**

---

## Step 6: Create OAuth 2.0 Credentials

1. In the left sidebar, click **"APIs & Services"** → **"Credentials"**
   - (Or go directly to: https://console.cloud.google.com/apis/credentials)
2. Click the blue **"+ CREATE CREDENTIALS"** button at the top
3. Select **"OAuth client ID"** from the dropdown
4. If prompted about OAuth consent screen, click **"Configure Consent Screen"** and complete Step 5 first
5. In the **"Application type"** dropdown, select **"Web application"**
6. Give it a name: `Calendar Sync Web Client`
7. **Authorized JavaScript origins:**
   - Click **"+ ADD URI"**
   - Enter: `http://localhost:8000`
8. **Authorized redirect URIs:**
   - Click **"+ ADD URI"**
   - Enter: `http://localhost:8000/auth/google/callback/`
   - **Important:** Make sure there's a trailing slash `/` at the end!
9. Click **"Create"**
10. A popup will appear with your credentials:
    - **Your Client ID:** (a long string ending in `.apps.googleusercontent.com`)
    - **Your Client Secret:** (a shorter string)
11. **IMPORTANT:** Copy both values now! You won't be able to see the secret again.
    - Click **"OK"** to close the popup

---

## Step 7: Add Credentials to .env File

1. Open your `.env` file in `OJT_project/`
2. Replace the placeholder values:

```
GOOGLE_CLIENT_ID=paste_your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=paste_your_client_secret_here
```

**Example:**
```
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
```

3. Save the file

---

## Step 8: Install Required Python Package

Make sure you have `python-dotenv` installed:

```bash
pip install python-dotenv
```

If you're in your virtual environment, it should already be installed. If not, run the command above.

---

## Step 9: Run Database Migrations

1. Open your terminal/command prompt
2. Navigate to your project: `cd OJT_project`
3. Activate your virtual environment (if not already active):
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
4. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

You should see output like:
```
Migrations for 'google_cal_sync':
  google_cal_sync/migrations/0001_initial.py
    - Create model GoogleToken
...
```

---

## Step 10: Create a Superuser (Optional but Recommended)

This lets you access Django admin to view stored tokens:

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

---

## Step 11: Start the Development Server

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
```

---

## Step 12: Test the OAuth Flow

1. Open your browser
2. Go to: **http://localhost:8000/login/**
3. You should see the login page with "Continue with Google" button
4. Click **"Continue with Google"**
5. You'll be redirected to Google's login page
6. Sign in with your Google account (the one you added as a test user)
7. You'll see a consent screen asking for calendar access
8. Click **"Allow"** or **"Continue"**
9. You'll be redirected back to: `http://localhost:8000/auth/google/callback/`
10. Then automatically redirected to: `http://localhost:8000/dashboard/`
11. You should see a success message: "Successfully connected to Google Calendar!"

---

## Step 13: Verify Token Storage

### Option A: Via Django Admin
1. Go to: **http://localhost:8000/admin/**
2. Log in with your superuser credentials
3. Click on **"Google Tokens"**
4. You should see your token entry with your username

### Option B: Via Settings Page
1. Go to: **http://localhost:8000/settings/**
2. You should see "Token Status: Active · Refreshes automatically"

---

## Troubleshooting

### Error: "OAuth setup error" or "GOOGLE_CLIENT_ID not found"
- **Solution:** Make sure your `.env` file is in `OJT_project/` folder (same level as `manage.py`)
- Check that variable names are exactly: `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- No spaces around the `=` sign

### Error: "redirect_uri_mismatch"
- **Solution:** Go back to Google Cloud Console → Credentials
- Edit your OAuth 2.0 Client ID
- Make sure redirect URI is exactly: `http://localhost:8000/auth/google/callback/`
- Must have trailing slash and match exactly (including `http://` not `https://`)

### Error: "access_denied" during OAuth
- **Solution:** Make sure you added your email as a test user in OAuth consent screen
- If using External user type, only test users can sign in during testing

### Token not saving
- **Solution:** Make sure migrations ran successfully
- Check that `db.sqlite3` file exists in `OJT_project/` folder
- Try running `python manage.py migrate` again

### "ModuleNotFoundError: No module named 'dotenv'"
- **Solution:** Install python-dotenv: `pip install python-dotenv`

---

## Next Steps

Once OAuth is working, you can:
1. Implement event creation API
2. Implement event listing API
3. Implement event update/delete APIs
4. Test with real Google Calendar events

---

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file to Git
- Add `.env` to your `.gitignore` file
- The Client Secret is sensitive - keep it private
- For production, use environment variables or a secrets manager
- Use HTTPS in production (not `http://localhost`)

---

## Quick Reference

**Key URLs:**
- Login: http://localhost:8000/login/
- OAuth Start: http://localhost:8000/auth/google/login/
- OAuth Callback: http://localhost:8000/auth/google/callback/
- Dashboard: http://localhost:8000/dashboard/
- Settings: http://localhost:8000/settings/
- Admin: http://localhost:8000/admin/

**Google Cloud Console:**
- Dashboard: https://console.cloud.google.com/
- APIs Library: https://console.cloud.google.com/apis/library
- Credentials: https://console.cloud.google.com/apis/credentials
- OAuth Consent: https://console.cloud.google.com/apis/credentials/consent

