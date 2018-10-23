import math
from logging import getLogger

from django.conf import settings
from django.contrib.messages import success
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from canto.services import (
    get_and_save_access_token,
    refresh_and_save_access_token,
    _get_oauth_state,
    disconnect_canto,
    _get_canto_settings,
    get_canto_client,
)
from .forms import CantoSettingsForm

logger = getLogger(__name__)


def paginate_canto_results(data, start, paginate_by):
    results_total = data["found"]
    results = data["results"]

    page = start // paginate_by + 1
    num_pages = math.ceil(results_total / paginate_by)

    context = {
        "results": results,
        "num_results": results_total,
        "page": page,
        "num_pages": num_pages,
    }

    if start > 0:
        context["previous_page_link"] = "?start={}".format(max(start - paginate_by, 0))

    if results_total > start + len(results):
        context["next_page_link"] = "?start={}".format(start + paginate_by)

    return context


@require_POST
def refresh_token(request, success_url=reverse_lazy("canto:settings")):
    refresh_and_save_access_token()
    success(request, _("Your canto token was refreshed."))
    return HttpResponseRedirect(success_url)


@require_POST
def disconnect(request, success_url=reverse_lazy("canto:settings")):
    disconnect_canto()
    success(request, _("Canto was disconnected."))
    return HttpResponseRedirect(success_url)


class CantoSettingsView(FormView):
    form_class = CantoSettingsForm
    template_name = "canto/settings.html"

    success_url = reverse_lazy("canto:settings")

    def dispatch(self, request, *args, **kwargs):
        self.canto_settings = _get_canto_settings()
        self.canto_client = get_canto_client(self.canto_settings)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = _("Canto settings")
        context["settings"] = self.canto_settings
        context["oauth_url"] = self.canto_client.get_oauth_url(
            _get_oauth_state(self.request.user),
            self.request.build_absolute_uri(self.request.path),
        )
        context["oauth_error_code"], context[
            "oauth_error_message"
        ] = self.get_oauth_error()

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = {
            "code": self.request.GET.get("code", ""),
            "state": self.request.GET.get("state", ""),
        }
        return kwargs

    def form_valid(self, form):
        get_and_save_access_token(
            form.cleaned_data["code"],
            state=form.cleaned_data["state"],
            expected_state=_get_oauth_state(self.request.user),
        )

        success(self.request, "Connected to canto!")
        return super().form_valid(form)

    def get_oauth_error(self):
        error_code = self.request.GET.get("error", "")
        error_message = self.request.GET.get("error_description", "")

        if error_code:
            logger.error(
                "An oauth error has occurred: %s %s", error_code, error_message
            )

        return error_code, error_message


class CantoTreeView(TemplateView):
    template_name = "canto/tree.html"
    title = _("Canto tree")

    def get_context_data(self, **kwargs):
        results = get_canto_client().get_tree()
        context = {"results": results, "title": self.title}
        context.update(kwargs)
        return super().get_context_data(**context)


class CantoAlbumView(TemplateView):
    paginate_by = 10
    album_id = None
    title = _("Canto album")
    template_name = "canto/album.html"

    def get_context_data(self, **kwargs):
        context = {"title": self.title}

        try:
            page = int(self.request.GET.get("page", 0))
        except ValueError:
            page = 0

        results = get_canto_client().get_album(
            self.kwargs["album_id"],
            page,
            self.paginate_by,
            settings.CANTO_FILTER_SCHEMES,
        )

        print(list(results))
        context.update({"results": results})
        context.update(kwargs)

        return super().get_context_data(**context)


class CantoSearchView(TemplateView):
    template_name = "canto/search.html"
    title = _("Canto search")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        query = self.request.GET.get("query", "")
        try:
            page = int(self.request.GET.get("page", 0))
        except ValueError:
            page = 0

        context = {}
        if query:
            context["results"] = get_canto_client().get_search_results(
                query, page, self.paginate_by, settings.CANTO_FILTER_SCHEMES
            )
        context.update(kwargs)
        return super().get_context_data(**context)


class CantoLibraryView(TemplateView):
    template_name = "canto/library.html"
    title = _("Canto library")
    album_id = None
    paginate_by = 10

    def get_context_data(self, **kwargs):
        canto_client = get_canto_client()
        tree_data = canto_client.get_tree()

        context = {"tree_items": tree_data, "title": self.title}

        album_id = self.kwargs.get("album_id")
        if album_id:
            try:
                page = int(self.request.GET.get("page", 0))
            except ValueError:
                page = 0

            album = canto_client.get_album(
                album_id, page, self.paginate_by, settings.CANTO_FILTER_SCHEMES
            )
            context["album"] = album

        context.update(kwargs)
        return super().get_context_data(**context)


@cache_control(max_age=300)
def canto_binary_view(request, url):
    public_url = get_canto_client().get_public_url_for_binary(url)
    return HttpResponseRedirect(public_url)
