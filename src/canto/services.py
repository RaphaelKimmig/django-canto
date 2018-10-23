import hashlib

from django.conf import settings

from canto.client import CantoClient
from canto.models import CantoSettings


def _get_canto_settings():
    return CantoSettings.objects.get_or_create()[0]


def get_canto_client(canto_settings: CantoSettings = None):
    canto_settings = canto_settings or _get_canto_settings()
    return CantoClient(
        api_url=settings.CANTO_API_URL,
        app_id=settings.CANTO_APP_ID,
        app_secret=settings.CANTO_APP_SECRET,
        oauth_url=settings.CANTO_OAUTH_URL,
        oauth_token_url=settings.CANTO_OAUTH_TOKEN_URL,
        access_token=canto_settings.access_token,
    )


def get_and_save_access_token(code, state, expected_state):
    if state != expected_state:
        # we ensure that the requested state matches the response state
        # https://auth0.com/docs/protocols/oauth2/oauth-state
        raise Exception("invalid state")

    access_token, valid_until, refresh_token = get_canto_client().create_access_token(
        code
    )

    CantoSettings.objects.update_or_create(
        defaults={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_valid_until": valid_until,
        }
    )


def refresh_and_save_access_token():
    canto_settings = _get_canto_settings()
    assert canto_settings.refresh_token
    access_token, valid_until, refresh_token = get_canto_client().refresh_access_token(
        canto_settings.refresh_token
    )
    canto_settings.access_token = access_token
    canto_settings.refresh_token = refresh_token
    canto_settings.token_valid_until = valid_until
    canto_settings.save()


def _get_oauth_state(user):
    """
    Local state that is passed to the oauth endpoint and back to ensure the response matches
    the request.
    """
    assert user.is_authenticated
    canto_settings = _get_canto_settings()
    return hashlib.sha512(
        "{}-{}".format(canto_settings.last_modified_at, user.pk).encode("utf-8")
    ).hexdigest()


def disconnect_canto():
    try:
        canto_settings = _get_canto_settings()
    except CantoSettings.DoesNotExist:
        return

    canto_settings.refresh_token = ""
    canto_settings.access_token = ""
    canto_settings.token_valid_until = None
    canto_settings.save()
