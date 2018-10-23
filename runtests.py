#!/usr/bin/env python
import os
import sys
import warnings
from optparse import OptionParser

import django
from django.conf import settings
from django.core.management import call_command


def runtests(test_path="canto"):
    if not settings.configured:
        DATABASES = {
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        }
        settings.configure(
            DATABASES=DATABASES,
            MIGRATION_MODULES={
                "canto": None,
                "auth": None,
                "admin": None,
                "contenttypes": None,
            },
            INSTALLED_APPS=(
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
                "canto",
            ),
            MIDDLEWARE_CLASSES=(),
            ROOT_URLCONF="canto.tests",
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [],
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ]
                    },
                }
            ],
        )

    django.setup()
    warnings.simplefilter("always", DeprecationWarning)
    failures = call_command(
        "test", test_path, interactive=False, failfast=False, verbosity=2
    )

    sys.exit(bool(failures))


if __name__ == "__main__":
    sys.path.append("./src")
    parser = OptionParser()
    (options, args) = parser.parse_args()
    runtests(*args)
