"""
Utility functions for Google OAuth2 and Calendar API operations.
"""
import os
from datetime import datetime, timedelta
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# OAuth2 scopes required for Google Calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_google_oauth_flow(request):
    """
    Create and configure Google OAuth2 flow.
    Returns a Flow instance ready for authorization.
    """
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")
    
    # Build redirect URI from request
    # Ensure consistent redirect URI (use localhost instead of 127.0.0.1)
    redirect_uri = request.build_absolute_uri('/auth/google/callback/')
    # Normalize to use localhost if it's 127.0.0.1
    if '127.0.0.1' in redirect_uri:
        redirect_uri = redirect_uri.replace('127.0.0.1', 'localhost')
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = redirect_uri
    
    return flow


def get_credentials_from_token(google_token):
    """
    Convert stored GoogleToken model to Google Credentials object.
    """
    credentials = Credentials(
        token=google_token.access_token,
        refresh_token=google_token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    )
    return credentials


def refresh_token_if_needed(google_token):
    """
    Check if token is expired and refresh it if needed.
    Updates the GoogleToken model with new access token.
    Returns True if token was refreshed, False if still valid.
    """
    if not google_token:
        return False
    
    # Check if token is expired (with 5 minute buffer)
    if google_token.token_expiry and google_token.token_expiry > datetime.now() + timedelta(minutes=5):
        return False  # Token still valid
    
    credentials = get_credentials_from_token(google_token)
    
    # Refresh the token
    credentials.refresh(Request())
    
    # Update the model
    google_token.access_token = credentials.token
    if credentials.refresh_token:
        google_token.refresh_token = credentials.refresh_token
    google_token.token_expiry = credentials.expiry
    google_token.save()
    
    return True


def get_calendar_service(user):
    """
    Get a Google Calendar API service instance for the user.
    Automatically refreshes token if needed.
    """
    from .models import GoogleToken
    
    try:
        google_token = GoogleToken.objects.get(user=user)
    except GoogleToken.DoesNotExist:
        return None
    
    # Refresh token if needed
    refresh_token_if_needed(google_token)
    
    # Get fresh credentials
    credentials = get_credentials_from_token(google_token)
    
    # Build and return the service
    service = build('calendar', 'v3', credentials=credentials)
    return service

