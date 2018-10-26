from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class CantoConfig(AppConfig):
    name = "canto"

    def ready(self):
        from django.conf import settings

        settings = settings._wrapped.__dict__

        settings.setdefault(
            "CANTO_OAUTH_URL", "https://oauth.canto.com:8443/oauth/api/oauth2/authorize"
        )
        settings.setdefault(
            "CANTO_OAUTH_TOKEN_URL",
            "https://oauth.canto.com:8443/oauth/api/oauth2/token",
        )
        settings.setdefault("CANTO_FILTER_SCHEMES", "")  # eg image or image|video

        if not settings.get("CANTO_API_URL"):
            raise ImproperlyConfigured("setting CANTO_API_URL is required.")
        if not settings.get("CANTO_APP_ID"):
            raise ImproperlyConfigured("setting CANTO_APP_ID is required.")
        if not settings.get("CANTO_APP_SECRET"):
            raise ImproperlyConfigured("setting CANTO_APP_SECRET is required.")

