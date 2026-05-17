from django.db import models
from django.db.models import Manager
from django.contrib.auth.models import BaseUserManager
from simple_history.models import HistoricalRecords

from AppCore.core.exceptions.exceptions import NotFoundException


class BaseManager(Manager):
    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except self.model.DoesNotExist as e:
            raise NotFoundException(f"{self.model._meta.verbose_name} não encontrado.")


class BaseManagerUser(BaseUserManager, BaseManager):
    pass

class BasicModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(inherit=True)
    
    objects = BaseManager()

    class Meta:
        abstract = True
