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
            SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",

            INSTALLED_APPS=(
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
                "canto",
            ),
            MIDDLEWARE=(
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
            ),
            ROOT_URLCONF="canto.tests.urls",
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
            CANTO_API_URL="https://canto-example.nosuchtold",
            CANTO_APP_ID="12345",
            CANTO_APP_SECRET="XXXXX",
            STATIC_URL="/static/",
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
