from django.conf.urls import url

from canto.views import (
    CantoSettingsView,
    refresh_token,
    disconnect,
    canto_binary_view,
    CantoLibraryView,
    CantoTreeView,
    CantoSearchView,
    CantoAlbumView,
)

app_name = "canto"
urlpatterns = [
    url(r"^canto/library/$", CantoLibraryView.as_view(), name="library"),
    url(
        r"^canto/library/(?P<album_id>.+)/$", CantoLibraryView.as_view(), name="library"
    ),
    url(r"^canto/settings/$", CantoSettingsView.as_view(), name="settings"),
    url(r"^canto/refresh/$", refresh_token, name="refresh-token"),
    url(r"^canto/disconnect/$", disconnect, name="disconnect"),
    url(r"^canto/tree/$", CantoTreeView.as_view(), name="tree"),
    url(r"^canto/search/$", CantoSearchView.as_view(), name="search"),
    url(r"^canto/album/(?P<album_id>.+)/$", CantoAlbumView.as_view(), name="album"),
    url(r"^canto/binary/(?P<url>.+)/$", canto_binary_view, name="binary"),
]
