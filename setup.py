from distutils.core import setup

setup(
    name="django-query-builder",
    version="0.5.3",
    packages=[
        'querybuilder'
    ],
    url="https://github.com/ambitioninc/django-query-builder",
    description="Django query builder",
    install_requires=[
        "django>=1.4",
        "pytz>=2012h"
    ]
)
