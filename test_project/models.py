from django.db import models


class Account(models.Model):
    """
    Account model
    """

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)