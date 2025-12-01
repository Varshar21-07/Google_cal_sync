"""
URL configuration for OJT_project project."""
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

def root_redirect(request):
    """Redirect root URL to login page."""
    return redirect('google_cal_sync:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),
    path('', include('google_cal_sync.urls')),
]
