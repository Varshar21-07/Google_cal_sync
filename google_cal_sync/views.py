from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from .models import GoogleToken
from .utils import (
    get_google_oauth_flow,
    authenticate_with_google,
    fetch_calendar_list,
    fetch_calendar_events,
    create_calendar_event,
    get_calendar_event,
    update_calendar_event,
    delete_calendar_event,
)


def parse_event_datetime(value):
    """
    Convert form datetime-local value to ISO string with timezone info.
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt.isoformat()


def format_datetime_for_input(iso_value):
    """
    Convert stored ISO datetime to value usable in datetime-local input.
    """
    if not iso_value:
        return ''
    cleaned = iso_value.replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return ''
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    local_dt = dt.astimezone(timezone.get_current_timezone())
    return local_dt.strftime("%Y-%m-%dT%H:%M")


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
    """Render the dashboard with live calendar data."""
    calendars = []
    events = []
    has_token = False
    api_error = None

    if request.user.is_authenticated:
        has_token = GoogleToken.objects.filter(user=request.user).exists()
        if has_token:
            service = authenticate_with_google(request.user)
            if service:
                try:
                    calendars = fetch_calendar_list(service)
                    primary_calendar = next((cal for cal in calendars if cal.get('primary')), None)
                    calendar_id = primary_calendar.get('id') if primary_calendar else 'primary'
                    events = fetch_calendar_events(service, calendar_id=calendar_id, max_results=5)
                except HttpError as error:
                    api_error = f"Google API error: {error}"
            else:
                api_error = "Connect your Google account to view calendars."

    context = {
        'has_token': has_token,
        'calendars': calendars,
        'events': events,
        'api_error': api_error,
    }
    return render(request, "google_cal_sync/dashboard.html", context)


def create_event_view(request):
    """Render the create event form and handle submissions."""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to create events.")
        return redirect('google_cal_sync:login')

    calendars = []
    api_error = None
    selected_calendar = request.POST.get('calendar_id', 'primary')
    form_values = {
        'title': request.POST.get('title', ''),
        'description': request.POST.get('description', ''),
        'start_time': request.POST.get('start_time', ''),
        'end_time': request.POST.get('end_time', ''),
        'location': request.POST.get('location', ''),
    }

    service = authenticate_with_google(request.user)
    if not service:
        messages.error(request, "Connect your Google account before creating events.")
        return redirect('google_cal_sync:login')

    try:
        calendars = fetch_calendar_list(service)
    except HttpError as error:
        api_error = f"Google API error: {error}"

    if request.method == 'POST' and not api_error:
        title = form_values['title'].strip()
        description = form_values['description'].strip()
        location = form_values['location'].strip() or None
        start_iso = parse_event_datetime(form_values['start_time'])
        end_iso = parse_event_datetime(form_values['end_time'])

        if not title or not start_iso or not end_iso:
            messages.error(request, "Title, start time, and end time are required.")
        else:
            try:
                created_event = create_calendar_event(
                    service,
                    selected_calendar or 'primary',
                    title,
                    description,
                    start_iso,
                    end_iso,
                    location,
                )
                messages.success(
                    request,
                    f"Event '{created_event['summary']}' created successfully."
                )
                return redirect('google_cal_sync:create_event')
            except HttpError as error:
                api_error = f"Google API error: {error}"
            except ValueError as error:
                api_error = str(error)

    context = {
        'calendars': calendars,
        'selected_calendar': selected_calendar,
        'api_error': api_error,
        'form_values': form_values,
        'mode': 'create',
    }
    return render(request, "google_cal_sync/create_event.html", context)


def update_event_view(request):
    """Allow editing an existing Google Calendar event."""
    if not request.user.is_authenticated:
        messages.error(request, "Please login to update events.")
        return redirect('google_cal_sync:login')

    calendar_id = request.GET.get('calendar_id') or request.POST.get('calendar_id') or 'primary'
    event_id = request.GET.get('event_id') or request.POST.get('event_id')

    if not event_id:
        messages.error(request, "Event ID missing.")
        return redirect('google_cal_sync:upcoming_events')

    service = authenticate_with_google(request.user)
    if not service:
        messages.error(request, "Connect your Google account before updating events.")
        return redirect('google_cal_sync:login')

    calendars = []
    api_error = None
    form_values = {
        'title': '',
        'description': '',
        'start_time': '',
        'end_time': '',
        'location': '',
    }

    try:
        calendars = fetch_calendar_list(service)
    except HttpError as error:
        api_error = f"Google API error: {error}"

    if not api_error:
        try:
            existing_event = get_calendar_event(service, calendar_id, event_id)
            if request.method == 'GET':
                form_values = {
                    'title': existing_event['summary'],
                    'description': existing_event['raw'].get('description', ''),
                    'start_time': format_datetime_for_input(existing_event['raw']['start'].get('dateTime')),
                    'end_time': format_datetime_for_input(existing_event['raw']['end'].get('dateTime')),
                    'location': existing_event['raw'].get('location', ''),
                }
        except HttpError as error:
            api_error = f"Google API error: {error}"

    if request.method == 'POST' and not api_error:
        form_values = {
            'title': request.POST.get('title', ''),
            'description': request.POST.get('description', ''),
            'start_time': request.POST.get('start_time', ''),
            'end_time': request.POST.get('end_time', ''),
            'location': request.POST.get('location', ''),
        }

        title = form_values['title'].strip()
        description = form_values['description'].strip()
        location = form_values['location'].strip() or None
        start_iso = parse_event_datetime(form_values['start_time'])
        end_iso = parse_event_datetime(form_values['end_time'])

        if not title or not start_iso or not end_iso:
            messages.error(request, "Title, start time, and end time are required.")
        else:
            try:
                update_calendar_event(
                    service,
                    calendar_id,
                    event_id,
                    title,
                    description,
                    start_iso,
                    end_iso,
                    location,
                )
                messages.success(request, "Event updated successfully.")
                return redirect('google_cal_sync:upcoming_events')
            except HttpError as error:
                api_error = f"Google API error: {error}"
            except ValueError as error:
                api_error = str(error)

    context = {
        'calendars': calendars,
        'selected_calendar': calendar_id,
        'api_error': api_error,
        'form_values': form_values,
        'event_id': event_id,
        'mode': 'update',
    }
    return render(request, "google_cal_sync/create_event.html", context)


def delete_event_view(request):
    """Delete an event from Google Calendar."""
    if request.method != 'POST':
        return redirect('google_cal_sync:upcoming_events')

    if not request.user.is_authenticated:
        messages.error(request, "Please login to delete events.")
        return redirect('google_cal_sync:login')

    calendar_id = request.POST.get('calendar_id') or 'primary'
    event_id = request.POST.get('event_id')

    if not event_id:
        messages.error(request, "Event ID missing.")
        return redirect('google_cal_sync:upcoming_events')

    service = authenticate_with_google(request.user)
    if not service:
        messages.error(request, "Connect your Google account before deleting events.")
        return redirect('google_cal_sync:login')

    try:
        delete_calendar_event(service, calendar_id, event_id)
        messages.success(request, "Event deleted successfully.")
    except HttpError as error:
        messages.error(request, f"Google API error: {error}")
    except ValueError as error:
        messages.error(request, str(error))

    return redirect('google_cal_sync:upcoming_events')


def upcoming_events_view(request):
    """Render a dedicated upcoming events section using live data."""
    events = []
    calendars = []
    selected_calendar = request.GET.get('calendar_id', 'primary')
    api_error = None
    has_token = False

    if request.user.is_authenticated:
        has_token = GoogleToken.objects.filter(user=request.user).exists()
        if has_token:
            service = authenticate_with_google(request.user)
            if service:
                try:
                    calendars = fetch_calendar_list(service)
                    events = fetch_calendar_events(
                        service,
                        calendar_id=selected_calendar,
                        max_results=20,
                    )
                except HttpError as error:
                    api_error = f"Google API error: {error}"
            else:
                api_error = "Connect your Google account to view events."

    context = {
        'events': events,
        'calendars': calendars,
        'selected_calendar': selected_calendar,
        'api_error': api_error,
        'has_token': has_token,
    }
    return render(request, "google_cal_sync/upcoming_events.html", context)


def settings_view(request):
    """Render settings with live token + calendar info."""
    has_token = False
    token_status = "Not connected"
    primary_calendar = None
    api_error = None

    if request.user.is_authenticated:
        try:
            google_token = GoogleToken.objects.get(user=request.user)
            has_token = True
            if google_token.token_expiry and google_token.token_expiry > timezone.now():
                token_status = "Active"
            else:
                token_status = "Expired"

            service = authenticate_with_google(request.user)
            if service:
                calendars = fetch_calendar_list(service)
                primary_calendar = next((cal for cal in calendars if cal.get('primary')), None)
        except GoogleToken.DoesNotExist:
            pass
        except HttpError as error:
            api_error = f"Google API error: {error}"

    context = {
        'has_token': has_token,
        'token_status': token_status,
        'primary_calendar': primary_calendar,
        'api_error': api_error,
    }
    return render(request, "google_cal_sync/settings.html", context)


def logout_view(request):
    """Log out the user and redirect to login page."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('google_cal_sync:login')
