from django.db import models
from django.utils import timezone


class CantoSettings(models.Model):
    class Meta:
        permissions = (("browse_library", "Can browse the canto library"),)

    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)

    token_valid_until = models.DateTimeField(null=True)

    last_modified_at = models.DateTimeField(auto_now=True)

    def is_connected(self):
        return self.access_token and self.token_valid_until > timezone.now()
