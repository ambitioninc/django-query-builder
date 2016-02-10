from django.contrib.postgres.fields import JSONField
from django.db import models


class User(models.Model):
    """
    User model
    """
    email = models.CharField(max_length=256)


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
    revenue = models.FloatField(null=True)
    margin = models.FloatField()
    margin_percent = models.FloatField()
    time = models.DateTimeField()


class MetricRecord(models.Model):
    """
    Example metric model
    """
    other_value = models.FloatField(default=0)
    data = JSONField()
