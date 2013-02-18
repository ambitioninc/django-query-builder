from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    """
    Account model
    """
    user = models.OneToOneField(User)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)


class Order(models.Model):
    """
    Order model
    """
    account = models.ForeignKey(Account)
    revenue = models.FloatField()
    margin = models.FloatField()
    margin_percent = models.FloatField()

