"""
Utility functions for Google OAuth2 and Calendar API operations.
"""
import os
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
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
    buffer_time = timezone.now() + timedelta(minutes=5)
    if google_token.token_expiry and google_token.token_expiry > buffer_time:
        return False  # Token still valid
    
    credentials = get_credentials_from_token(google_token)
    
    # Refresh the token
    credentials.refresh(Request())
    
    # Update the model
    google_token.access_token = credentials.token
    if credentials.refresh_token:
        google_token.refresh_token = credentials.refresh_token
    credentials_expiry = credentials.expiry or (timezone.now() + timedelta(hours=1))
    google_token.token_expiry = credentials_expiry
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


def authenticate_with_google(user):
    """
    Convenience helper that returns an authenticated Calendar service.
    """
    return get_calendar_service(user)


def fetch_calendar_list(service):
    """
    Fetch the user's calendar list.
    """
    if not service:
        return []

    response = service.calendarList().list().execute()
    return response.get('items', [])


def get_writable_calendars(service):
    """
    Fetch only calendars where the user has write access (owner or writer).
    Filters out read-only calendars like public holiday calendars.
    """
    all_calendars = fetch_calendar_list(service)
    writable_calendars = []
    
    for calendar in all_calendars:
        access_role = calendar.get('accessRole', '').lower()
        # Only include calendars where user can write
        if access_role in ['owner', 'writer']:
            writable_calendars.append(calendar)
    
    return writable_calendars


def fetch_calendar_events(service, calendar_id='primary', time_min=None, max_results=10):
    """
    Fetch upcoming events for the specified calendar.
    """
    if not service:
        return []

    if not time_min:
        time_min = timezone.now().isoformat()

    events_response = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_response.get('items', [])
    return [normalize_event(event) for event in events]


def normalize_event(event):
    """
    Prepare event dictionary with safe fields for templates.
    """
    start = event.get('start', {}) or {}
    end = event.get('end', {}) or {}

    return {
        'id': event.get('id'),
        'summary': event.get('summary', 'Untitled event'),
        'start_text': start.get('dateTime') or start.get('date') or 'No start time',
        'end_text': end.get('dateTime') or end.get('date'),
        'location': event.get('location'),
        'status': event.get('status'),
        'raw': event,
    }


def create_calendar_event(service, calendar_id, summary, description, start_iso, end_iso, location=None):
    """
    Create a new calendar event for the user.
    """
    if not service:
        raise ValueError("Google Calendar service is not available.")

    tz_name = timezone.get_current_timezone_name()

    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_iso,
            'timeZone': tz_name,
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': tz_name,
        },
    }

    if location:
        event_body['location'] = location

    created_event = service.events().insert(
        calendarId=calendar_id or 'primary',
        body=event_body
    ).execute()

    return normalize_event(created_event)


def get_calendar_event(service, calendar_id, event_id):
    """
    Retrieve a single calendar event.
    """
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    return normalize_event(event)


def update_calendar_event(service, calendar_id, event_id, summary, description, start_iso, end_iso, location=None):
    """
    Update an existing calendar event.
    """
    if not service:
        raise ValueError("Google Calendar service is not available.")

    tz_name = timezone.get_current_timezone_name()
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_iso,
            'timeZone': tz_name,
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': tz_name,
        },
    }

    if location:
        event_body['location'] = location

    updated_event = service.events().patch(
        calendarId=calendar_id,
        eventId=event_id,
        body=event_body
    ).execute()

    return normalize_event(updated_event)


def delete_calendar_event(service, calendar_id, event_id):
    """
    Delete an event from the user's calendar.
    """
    if not service:
        raise ValueError("Google Calendar service is not available.")

    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

