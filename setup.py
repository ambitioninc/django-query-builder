from distutils.core import setup

setup(
    name="django-query-builder",
    version="0.4.1",
    packages=[
        'querybuilder'
    ],
    url="https://github.com/wesokes/django-query-builder",
    description="Django query builder",
    install_requires=[
        "django>=1.5.2",
        "pytz==2012h"
    ]
)
