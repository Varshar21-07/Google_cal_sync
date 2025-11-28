from django.db import models
from django.contrib.auth.models import User


class GoogleToken(models.Model):
    """Stores Google OAuth2 access and refresh tokens for each user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_token')
    access_token = models.TextField(help_text="Google OAuth2 access token")
    refresh_token = models.TextField(help_text="Google OAuth2 refresh token")
    token_expiry = models.DateTimeField(help_text="When the access token expires")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Google Token"
        verbose_name_plural = "Google Tokens"

    def __str__(self):
        return f"GoogleToken for {self.user.username}"
