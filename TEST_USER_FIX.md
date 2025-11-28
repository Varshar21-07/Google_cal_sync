# Fix "Access Blocked" Error - Add Test User

## The Problem
Google is blocking access because your app is in "Testing" mode and your email is not listed as a test user.

## Solution: Add Yourself as a Test User

### Step 1: Go to OAuth Consent Screen
1. Open: **https://console.cloud.google.com/apis/credentials/consent**
2. Or navigate: **APIs & Services** → **OAuth consent screen**

### Step 2: Add Test Users
1. Scroll down to the **"Test users"** section
2. Click **"+ ADD USERS"** button
3. Enter your email address: **varshar9483@gmail.com**
4. Click **"Add"**
5. Your email should now appear in the test users list

### Step 3: Save Changes
- The changes are saved automatically
- Wait 1-2 minutes for changes to take effect

### Step 4: Try Again
1. Go back to: `http://localhost:8000/login/`
2. Click "Continue with Google"
3. You should now be able to sign in!

## Important Notes

- **For Development:** You can add up to 100 test users
- **Test users only:** Only emails in the test users list can sign in while the app is in "Testing" mode
- **No verification needed:** For development/testing, you don't need to verify the app with Google
- **Production:** If you want to make the app public later, you'll need to go through Google's verification process

## Alternative: Publish the App (Not Recommended for Development)

If you want anyone to be able to sign in (not just test users), you can:
1. Go to OAuth consent screen
2. Click **"PUBLISH APP"** button at the top
3. Confirm the warning

**Note:** Publishing makes your app available to all Google users, but you'll still need to complete verification if you want to use sensitive scopes like Calendar access.

