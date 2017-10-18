"""
WSGI config for foodtasker project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodtasker.settings")

application = get_wsgi_application()

#Use witenoise pacage to serve static files on Heroku

application = DjangoWhiteNoise(application)
