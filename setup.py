from distutils.core import setup

setup(
    name="django-query-builder",
    version="0.4.0",
    packages=[
        'querybuilder'
    ],
    url="https://github.com/wesokes/django-query-builder",
    description="Django query builder",
    install_requires=[
        "django>=1.4",
        "pytz==2012h"
    ]
)
