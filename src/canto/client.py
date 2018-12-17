import math
from datetime import timedelta
from json import JSONDecodeError
from logging import getLogger
from urllib.parse import urlencode

import requests

try:
    from django.utils.timezone import now
except ImportError:
    import datetime

    now = datetime.datetime.now

logger = getLogger(__name__)


class ApiException(Exception):
    pass


class ResourceNotFound(ApiException):
    pass


class CantoClient:
    def __init__(
        self, api_url, app_id, app_secret, oauth_url, oauth_token_url, access_token
    ):
        self.api_url = api_url
        self.app_id = app_id
        self.app_secret = app_secret
        self.oauth_url = oauth_url
        self.oauth_token_url = oauth_token_url
        self.access_token = access_token

    def create_access_token(self, code):
        params = {
            "code": code,
            "app_secret": self.app_secret,
            "grant_type": "authorization_code",
            "app_id": self.app_id,
        }
        url = "{}?{}".format(self.oauth_token_url, urlencode(params))

        request_time = now()
        response = requests.post(url)

        if response.ok:
            data = response.json()
            access_token = data["accessToken"]  # valid for one month

            expires_in_seconds = int(data["expiresIn"])
            valid_until = request_time + timedelta(seconds=expires_in_seconds)
            refresh_token = data["refreshToken"]  # valid for one year
            return access_token, valid_until, refresh_token
        else:
            try:
                data = response.json()
                error_code = data["error"]
                error_description = data["error_description"]
            except JSONDecodeError:
                error_code = ""
                error_description = response.content

            logger.error(
                "An error occurred getting an access token: %s %s",
                error_code,
                error_description,
            )
            raise ApiException("Error getting access token")

    def refresh_access_token(self, refresh_token):
        params = {
            "app_secret": self.app_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "app_id": self.app_id,
        }
        url = "{}?{}".format(self.oauth_token_url, urlencode(params))

        request_time = now()
        response = requests.post(url)

        if response.ok:
            data = response.json()
            access_token = data["accessToken"]  # valid for one month
            expires_in_seconds = int(data["expiresIn"])
            valid_until = request_time + timedelta(seconds=expires_in_seconds)
            refresh_token = data["refreshToken"]  # valid for one year
            return access_token, valid_until, refresh_token
        else:
            try:
                data = response.json()
                error_code = data["error"]
                error_description = data["error_description"]
            except JSONDecodeError:
                error_code = ""
                error_description = response.content

            logger.error(
                "An error occurred getting an access token: %s %s",
                error_code,
                error_description,
            )
            raise ApiException("Error getting access token")

    def _authenticated_request(self, url, params=None, **kwargs):
        assert self.access_token, "an access token is required"
        if not url.startswith(self.api_url):
            url = self.api_url + url

        if params:
            url += "?" + urlencode(params)

        response = requests.get(
            url,
            headers={
                "Authorization": "Bearer {}".format(self.access_token),
                "User-Agent": self.app_id,
            },
            **kwargs,
        )

        if response.ok:
            return response
        elif response.status_code == 404:
            raise ResourceNotFound()
        else:
            raise ApiException(
                "response status code was {}".format(response.status_code)
            )

    def get_oauth_url(self, state, redirect_uri):
        params = {
            "response_type": "code",
            "app_id": self.app_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return "{}?{}".format(self.oauth_url, urlencode(params))

    def get_album(
        self,
        album_id,
        start,
        paginate_by,
        scheme,
        sort_by="time",
        sort_direction="descending",
    ):
        # start = max(page - 1, 0) * paginate_by
        params = {
            "limit": paginate_by,
            "start": start,
            "scheme": scheme,
            "sortBy": sort_by,
            "sortDirection": sort_direction,
        }

        album_data = self._authenticated_request(
            "/api/v1/album/{}".format(album_id), params
        ).json()

        return album_data

    def get_search_results(
        self,
        query,
        start,
        paginate_by,
        scheme,
        sort_by="time",
        sort_direction="descending",
    ):
        params = {
            "limit": paginate_by,
            "start": start,
            "keyword": query,
            "scheme": scheme,
            "sortBy": sort_by,
            "sortDirection": sort_direction,
        }

        search_results = self._authenticated_request("/api/v1/search", params).json()

        return search_results

    def get_image(self, image_id):
        image_data = self._authenticated_request(
            "/api/v1/image/{}".format(image_id)
        ).json()

        return image_data

    def get_binary(self, url):
        assert url.startswith(self.api_url + "/api_binary/")
        response = self._authenticated_request(url, allow_redirects=True)
        return response.content

    def get_public_url_for_binary(self, url):
        assert url.startswith(self.api_url + "/api_binary/"), (
            url,
            self.api_url + "/api_binary/",
        )
        response = self._authenticated_request(url, allow_redirects=False)

        if not response.status_code == 302:
            raise ApiException(
                "Unexpected response code {}, expected a redirect".format(
                    response.status_code
                )
            )

        return response.headers["Location"]

    def get_tree(self):
        return self._authenticated_request(
            "/api/v1/tree", {"sortBy": "name", "sortDirection": "ascending"}
        ).json()
