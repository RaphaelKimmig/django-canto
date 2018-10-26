from datetime import timedelta

import mock
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django_dynamic_fixture import G
from django_webtest import WebTest

from canto.services import _get_oauth_state, _get_canto_settings, get_canto_client


class FakeResponse:
    def __init__(self, data, ok=True) -> None:
        super().__init__()
        self.data = data
        self.ok = ok

    def json(self):
        return self.data


@override_settings(
    CANTO_API_URL="https://example.canto.com",
    CANTO_APP_ID="XXX",
    CANTO_APP_SECRET="ZZZ",
)
class CantoViewTest(WebTest):
    def setUp(self):
        self.user = G(get_user_model())
        self.user.user_permissions.add(Permission.objects.get(codename='browse_library'))
        self.user.user_permissions.add(Permission.objects.get(codename='change_cantosettings'))

    def test_settings_default_to_not_connected(self):
        response = self.app.get(reverse("canto:settings"), user=self.user)
        self.assertContains(response, "You are not connected")
        self.assertContains(
            response,
            escape(
                get_canto_client().get_oauth_url(
                    _get_oauth_state(self.user), response.request.url
                )
            ),
        )

    def test_settings_permissions(self):
        unauthorized_user = G(get_user_model())
        self.app.get(reverse('canto:settings'), user=unauthorized_user, status=403)
        self.app.post(reverse('canto:disconnect'), user=unauthorized_user, status=403)
        self.app.post(reverse('canto:refresh-token'), user=unauthorized_user, status=403)

    def test_browse_permissions(self):
        unauthorized_user = G(get_user_model())
        self.app.get(reverse('canto:library'), user=unauthorized_user, status=403)
        self.app.get(reverse('canto:tree-json'), user=unauthorized_user, status=403)
        self.app.get(reverse('canto:search-json', kwargs={'query': 'something'}), user=unauthorized_user, status=403)
        self.app.get(reverse('canto:album-json', kwargs={'album_id': '123'}), user=unauthorized_user, status=403)
        self.app.get(reverse('canto:binary', kwargs={'url': 'foo'}), user=unauthorized_user, status=403)

    def test_oauth_confirmation_view(self):
        oauth_state = _get_oauth_state(self.user)
        settings_page = self.app.get(
            reverse("canto:settings") + "?code=CANTO_CODE&state=" + oauth_state, user=self.user
        )
        self.assertContains(settings_page, "Please confirm the connection to canto")

        canto_response = FakeResponse(
            {
                "accessToken": "i-grant-access",
                "state": oauth_state,
                "expiresIn": 3600,
                "refreshToken": "feel-refreshed",
            }
        )
        now = timezone.now()

        with mock.patch("canto.client.requests.post", return_value=canto_response):
            with mock.patch("canto.client.now", return_value=now):
                confirm_response = settings_page.form.submit()

        self.assertContains(confirm_response.follow(), "You are connected to canto")

        canto_settings = _get_canto_settings()
        self.assertEqual(canto_settings.access_token, "i-grant-access")
        self.assertEqual(canto_settings.refresh_token, "feel-refreshed")
        self.assertEqual(
            canto_settings.token_valid_until, now + timedelta(seconds=3600)
        )

    def test_oauth_disconnect_view(self):
        canto_settings = _get_canto_settings()
        canto_settings.refresh_token = "refresh"
        canto_settings.access_token = "access"
        canto_settings.token_valid_until = timezone.now() + timedelta(seconds=3600)
        canto_settings.save()

        response = self.app.get(reverse("canto:settings"), user=self.user)
        self.assertContains(response, "You are connected to canto")

        response = response.forms["canto-disconnect"].submit()
        self.assertContains(response.follow(), "You are not connected")
