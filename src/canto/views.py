from logging import getLogger

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages import success
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views import View
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


@permission_required("canto.change_cantosettings", raise_exception=True)
@require_POST
def refresh_token(request, success_url=reverse_lazy("canto:settings")):
    refresh_and_save_access_token()
    success(request, _("Your canto token was refreshed."))
    return HttpResponseRedirect(success_url)


@permission_required("canto.change_cantosettings", raise_exception=True)
@require_POST
def disconnect(request, success_url=reverse_lazy("canto:settings")):
    disconnect_canto()
    success(request, _("Canto was disconnected."))
    return HttpResponseRedirect(success_url)


class CantoSettingsView(PermissionRequiredMixin, FormView):
    permission_required = "canto.change_cantosettings"
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


class CantoLibraryView(PermissionRequiredMixin, TemplateView):
    permission_required = "canto.browse_library"
    template_name = "canto/library.html"
    title = _("Canto library")
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = {"title": self.title}
        context.update(kwargs)
        return super().get_context_data(**context)


@permission_required("canto.browse_library", raise_exception=True)
@cache_control(max_age=300)
def canto_binary_view(request, url):
    # double slashed may be stripped by the web server
    if url.startswith('https:/') and not url.startswith('https://'):
        url = 'https://' + url[len('https:/'):]
    public_url = get_canto_client().get_public_url_for_binary(url)
    return HttpResponseRedirect(public_url)


class CantoTreeJsonView(PermissionRequiredMixin, View):
    permission_required = "canto.browse_library"

    def get(self, request, **kwargs):
        results = get_canto_client().get_tree()
        return JsonResponse(results)


class CantoAlbumJsonView(PermissionRequiredMixin, View):
    permission_required = "canto.browse_library"
    paginate_by = 100
    album_id = None

    def get(self, request, **kwargs):
        try:
            start = int(request.GET.get("start", 0))
        except ValueError:
            start = 0

        results = get_canto_client().get_album(
            self.kwargs["album_id"],
            start,
            self.paginate_by,
            settings.CANTO_FILTER_SCHEMES,
        )

        return JsonResponse(results)


class CantoSearchJsonView(PermissionRequiredMixin, View):
    permission_required = "canto.browse_library"
    paginate_by = 100

    def get(self, request, **kwargs):
        try:
            start = int(request.GET.get("start", 0))
        except ValueError:
            start = 0

        results = get_canto_client().get_search_results(
            kwargs["query"], start, self.paginate_by, settings.CANTO_FILTER_SCHEMES
        )

        return JsonResponse(results)
