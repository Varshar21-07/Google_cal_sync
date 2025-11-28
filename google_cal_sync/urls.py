from django.urls import path

from . import views

app_name = "google_cal_sync"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("auth/google/login/", views.google_oauth_login, name="google_oauth_login"),
    path("auth/google/callback/", views.google_oauth_callback, name="google_oauth_callback"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("events/create/", views.create_event_view, name="create_event"),
    path("events/upcoming/", views.upcoming_events_view, name="upcoming_events"),
    path("settings/", views.settings_view, name="settings"),
]

