try:
    from django.contrib.postgres.fields import JSONField
except ImportError:
    from jsonfield import JSONField
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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)


class Order(models.Model):
    """
    Order model
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
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


class Uniques(models.Model):
    """
    For testing upserts
    """
    field1 = models.CharField(unique=True, max_length=16)
    field2 = models.CharField(unique=True, max_length=16)
    field3 = models.CharField(max_length=16)
    field4 = models.CharField(max_length=16, default='default_value')
    field5 = models.CharField(max_length=16, null=True, default=None)
    field6 = models.CharField(max_length=16)
    field7 = models.CharField(max_length=16)
    field8 = JSONField(default={})
    custom_field_name = models.CharField(
        max_length=16, null=True, default='foo', db_column='actual_db_column_name'
    )

    class Meta:
        unique_together = ('field6', 'field7')
