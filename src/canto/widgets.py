from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


class CantoImageWidget(ForeignKeyRawIdWidget):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        rel_to = self.rel.model
        if rel_to in self.admin_site._registry:
            # The related object is registered with the same AdminSite
            related_url = reverse("canto:library")
            context["related_url"] = mark_safe(related_url)
            context["link_title"] = _("Lookup")
        return context

    def __init__(self, rel, admin_site, attrs=None, using=None):
        attrs = attrs or {}
        attrs['data-canto-image'] = 'true'
        super().__init__(rel, admin_site, attrs, using)
