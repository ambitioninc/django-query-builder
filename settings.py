import os

from django.conf import settings


print('this is the settings file')
print(os.environ)


def configure_settings():
    """
    Configures settings for manage.py and for run_tests.py.
    """
    print('this is the configure settings')
    print(os.environ)
    if not settings.configured:
        # Determine the database settings depending on if a test_db var is set in CI mode or not
        print('-' * 20)
        print('os environ')
        print(os.environ)
        print(os.environ.get('DB'))
        test_db = os.environ.get('DB', None)
        if test_db is None:
            db_config = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'ambition',
                'USER': 'ambition',
                'PASSWORD': 'ambition',
                'HOST': 'db'
            }
        elif test_db == 'postgres':
            db_config = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'postgres',
                'NAME': 'querybuilder',
            }
        else:
            raise RuntimeError('Unsupported test DB {0}'.format(test_db))

        settings.configure(
            TEST_RUNNER='django_nose.NoseTestSuiteRunner',
            NOSE_ARGS=['--nocapture', '--nologcapture', '--verbosity=1'],
            MIDDLEWARE_CLASSES=(),
            DATABASES={
                'default': db_config,
                'mock-second-database': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'TEST_MIRROR': 'default',
                },
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
