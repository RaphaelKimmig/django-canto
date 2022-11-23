from django.urls import re_path

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
    re_path(r"^canto/settings/$", CantoSettingsView.as_view(), name="settings"),
    re_path(r"^canto/refresh/$", refresh_token, name="refresh-token"),
    re_path(r"^canto/disconnect/$", disconnect, name="disconnect"),
    re_path(r"^canto/library/$", CantoLibraryView.as_view(), name="library"),
    re_path(r"^canto/tree.json$", CantoTreeJsonView.as_view(), name="tree-json"),
    re_path(
        r"^canto/search/(?P<query>.+).json$",
        CantoSearchJsonView.as_view(),
        name="search-json",
    ),
    re_path(
        r"^canto/album/(?P<album_id>.+).json$",
        CantoAlbumJsonView.as_view(),
        name="album-json",
    ),
    re_path(r"^canto/binary/(?P<url>.+)$", canto_binary_view, name="binary"),
]
