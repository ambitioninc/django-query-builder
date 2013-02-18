from django.contrib.admin import site
import models


site.register(models.Account)
site.register(models.Order)
site.register(models.User)
