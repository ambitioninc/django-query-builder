import copy
import os

from django.conf import settings


def configure_settings():
    """
    Configures settings for manage.py and for run_tests.py.
    """
    if not settings.configured:
        # Determine the database settings depending on if a test_db var is set in CI mode or not
        test_db = os.environ.get('DB', None)
        if test_db is None:
            db_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'ambition_test',
                'USER': 'postgres',
                'PASSWORD': '',
                'HOST': 'db',
            }
        elif test_db == 'postgres':
            # db_config = {
            #     'ENGINE': 'django.db.backends.postgresql',
            #     'NAME': 'querybuilder',
            #     'USER': 'postgres',
            #     'PASSWORD': '',
            #     'HOST': 'db',
            # }
            db_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'querybuilder',
                'USER': 'travis',
                'PORT': '5433',
            }
        elif test_db == 'sqlite':
            db_config = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'regex_field',
            }
        else:
            raise RuntimeError('Unsupported test DB {0}'.format(test_db))

        db_config2 = copy.copy(db_config)
        db_config2['NAME'] = f'{db_config2["NAME"]}2'
        db_config2['TEST_MIRROR'] = 'default'

        settings.configure(
            TEST_RUNNER='django_nose.NoseTestSuiteRunner',
            NOSE_ARGS=['--nocapture', '--nologcapture', '--verbosity=1'],
            MIDDLEWARE_CLASSES=(),
            DATABASES={
                'default': db_config,
                'mock-second-database': db_config2,
            },
            INSTALLED_APPS=(
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'querybuilder',
                'querybuilder.tests',
            ),
            ROOT_URLCONF='querybuilder.urls',
            TIME_ZONE='UTC',
            USE_TZ=False,
        )
