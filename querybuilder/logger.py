
from django.conf import settings
from django.db import connection
settings.DEBUG = True
settings.DEBUG = False

connection.queries