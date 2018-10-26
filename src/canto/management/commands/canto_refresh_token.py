from django.core.management.base import BaseCommand

from ...services import refresh_and_save_access_token


class Command(BaseCommand):
    def handle(self, *args, **options):
        refresh_and_save_access_token()
