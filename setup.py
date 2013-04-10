from distutils.core import setup
from setuptools import find_packages

setup(
    name="django-query-builder",
    version="0.2.6",
    packages=find_packages(),
    url="https://github.com/wesokes/django-query-builder",
    description="Django query builder",
    install_requires=[
        "django>=1.4",
    ]
)
