from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import GoogleToken
from .utils import get_google_oauth_flow, get_credentials_from_token


def login_view(request):
    """Render the static login page."""
    return render(request, "google_cal_sync/login.html")


def google_oauth_login(request):
    """
    Initiate Google OAuth2 flow.
    Redirects user to Google's authorization page.
    """
    try:
        flow = get_google_oauth_flow(request)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        # Store state in session for security
        request.session['oauth_state'] = state
        request.session.modified = True  # Mark session as modified
        request.session.save()  # Ensure session is saved
        
        # Debug: Print state for troubleshooting
        if settings.DEBUG:
            print(f"OAuth state stored: {state[:20]}...")
        
        return redirect(authorization_url)
    except ValueError as e:
        # Missing environment variables
        messages.error(request, f"Configuration error: {str(e)}. Please check your .env file.")
        return redirect('google_cal_sync:login')
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"OAuth Error: {error_details}")  # Print to console for debugging
        messages.error(request, f"OAuth setup error: {str(e)}. Check server console for details.")
        return redirect('google_cal_sync:login')


def google_oauth_callback(request):
    """
    Handle Google OAuth2 callback.
    Exchanges authorization code for tokens and stores them.
    """
    # Get authorization code from callback
    code = request.GET.get('code')
    if not code:
        error = request.GET.get('error', 'Unknown error')
        messages.error(request, f"Authorization failed: {error}")
        return redirect('google_cal_sync:login')
    
    # Get state from session
    state = request.session.get('oauth_state')
    # Also get state from request (Google sends it back)
    request_state = request.GET.get('state')
    
    # Validate state if we have it in session
    if state and request_state and state != request_state:
        messages.error(request, "OAuth state mismatch. Security check failed. Please try again.")
        # Clear the session state
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
        return redirect('google_cal_sync:login')
    
    # If no state in session, we'll proceed anyway (for development)
    # In production, you might want to be stricter
    if not state:
        print("Warning: OAuth state not found in session, but proceeding anyway...")
    
    try:
        flow = get_google_oauth_flow(request)
        # Use state from request if available, otherwise from session
        state_to_use = request_state or state
        flow.fetch_token(code=code, state=state_to_use)
        
        credentials = flow.credentials
        
        # Get or create user (for demo, we'll use a default user or create one)
        # In production, you'd match this to your user system
        user, created = User.objects.get_or_create(
            username='google_user',
            defaults={'email': ''}
        )
        
        # Calculate token expiry
        # credentials.expiry is already a datetime object, not seconds
        if credentials.expiry:
            token_expiry = credentials.expiry
        else:
            # If no expiry provided, default to 1 hour from now
            token_expiry = datetime.now() + timedelta(hours=1)
        
        # Save or update tokens
        google_token, created = GoogleToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': token_expiry,
            }
        )
        
        # Clear the OAuth state from session
        if 'oauth_state' in request.session:
            del request.session['oauth_state']
            request.session.save()
        
        # Log the user in
        login(request, user)
        
        messages.success(request, "Successfully connected to Google Calendar!")
        return redirect('google_cal_sync:dashboard')
        
    except Exception as e:
        messages.error(request, f"Token exchange failed: {str(e)}")
        return redirect('google_cal_sync:login')


def dashboard_view(request):
    """Render the dashboard layout preview."""
    # Check if user has Google token
    has_token = False
    if request.user.is_authenticated:
        has_token = GoogleToken.objects.filter(user=request.user).exists()
    
    context = {
        'has_token': has_token,
    }
    return render(request, "google_cal_sync/dashboard.html", context)


def create_event_view(request):
    """Render the create event form preview."""
    return render(request, "google_cal_sync/create_event.html")


def upcoming_events_view(request):
    """Render a dedicated upcoming events section."""
    return render(request, "google_cal_sync/upcoming_events.html")


def settings_view(request):
    """Render placeholder settings content."""
    has_token = False
    token_status = "Not connected"
    if request.user.is_authenticated:
        try:
            google_token = GoogleToken.objects.get(user=request.user)
            has_token = True
            # Use timezone-aware datetime for comparison
            if google_token.token_expiry and google_token.token_expiry > timezone.now():
                token_status = "Active"
            else:
                token_status = "Expired"
        except GoogleToken.DoesNotExist:
            pass
    
    context = {
        'has_token': has_token,
        'token_status': token_status,
    }
    return render(request, "google_cal_sync/settings.html", context)
