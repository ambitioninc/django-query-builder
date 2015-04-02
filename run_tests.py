"""
Provides the ability to run test on a standalone Django app.
"""
import sys
from optparse import OptionParser

import django
from django.conf import settings

from settings import configure_settings

# Configure the default settings
configure_settings()
if django.VERSION[1] >= 7:
    django.setup()

# Django nose must be imported here since it depends on the settings being configured
from django_nose import NoseTestSuiteRunner


def run_tests(*test_args, **kwargs):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['querybuilder']

    kwargs.setdefault('interactive', False)

    test_runner = NoseTestSuiteRunner(**kwargs)

    failures = test_runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--verbosity', dest='verbosity', action='store', default=1, type=int)
    parser.add_options(NoseTestSuiteRunner.options)
    (options, args) = parser.parse_args()

    run_tests(*args, **options.__dict__)
