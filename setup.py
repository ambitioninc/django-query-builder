# import multiprocessing to avoid this bug (http://bugs.python.org/issue15881#msg170215)
import multiprocessing
assert multiprocessing
import re
from setuptools import setup, find_packages


def get_version():
    """
    Extracts the version number from the version.py file.
    """
    VERSION_FILE = 'querybuilder/version.py'
    mo = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', open(VERSION_FILE, 'rt').read(), re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError('Unable to find version string in {0}.'.format(VERSION_FILE))


setup(
    name='django-query-builder',
    version=get_version(),
    description='Build complex nested queries',
    long_description=open('README.rst').read(),
    url='https://github.com/ambitioninc/django-query-builder',
    author='Wes Okes',
    author_email='wes.okes@gmail.com',
    keywords='django, database, query, sql, postgres, upsert',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Development Status :: 5 - Production/Stable',
    ],
    license='MIT',
    install_requires=[
        'django>=1.7',
        'pytz>=2015.6',
        'fleming>=0.4.3',
        'six',
    ],
    tests_require=[
        'psycopg2',
        'django-nose>=1.4',
        'mock==1.0.1',
        'django-dynamic-fixture==1.8.5',
        'jsonfield==0.9.20'
    ],
    test_suite='run_tests.run_tests',
    include_package_data=True,
)
