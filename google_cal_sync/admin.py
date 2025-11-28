from django.contrib import admin
from .models import GoogleToken


@admin.register(GoogleToken)
class GoogleTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_expiry', 'created_at', 'updated_at')
    list_filter = ('created_at', 'token_expiry')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
