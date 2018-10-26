from django.conf.urls import url

from canto.views import (
    CantoSettingsView,
    refresh_token,
    disconnect,
    canto_binary_view,
    CantoLibraryView,
    CantoAlbumJsonView,
    CantoTreeJsonView,
    CantoSearchJsonView,
)

app_name = "canto"
urlpatterns = [
    url(r"^canto/settings/$", CantoSettingsView.as_view(), name="settings"),
    url(r"^canto/refresh/$", refresh_token, name="refresh-token"),
    url(r"^canto/disconnect/$", disconnect, name="disconnect"),
    url(r"^canto/library/$", CantoLibraryView.as_view(), name="library"),
    url(r"^canto/tree.json$", CantoTreeJsonView.as_view(), name="tree-json"),
    url(
        r"^canto/search/(?P<query>.+).json$",
        CantoSearchJsonView.as_view(),
        name="search-json",
    ),
    url(
        r"^canto/album/(?P<album_id>.+).json$",
        CantoAlbumJsonView.as_view(),
        name="album-json",
    ),
    url(r"^canto/binary/(?P<url>.+)$", canto_binary_view, name="binary"),
]
