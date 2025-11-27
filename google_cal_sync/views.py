from django.shortcuts import render


def login_view(request):
    """Render the static login page."""
    return render(request, "google_cal_sync/login.html")


def dashboard_view(request):
    """Render the dashboard layout preview."""
    return render(request, "google_cal_sync/dashboard.html")


def create_event_view(request):
    """Render the create event form preview."""
    return render(request, "google_cal_sync/create_event.html")


def upcoming_events_view(request):
    """Render a dedicated upcoming events section."""
    return render(request, "google_cal_sync/upcoming_events.html")


def settings_view(request):
    """Render placeholder settings content."""
    return render(request, "google_cal_sync/settings.html")
