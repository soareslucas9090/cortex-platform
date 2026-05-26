from django.db import models
from django.db.models import Manager
from django.contrib.auth.models import BaseUserManager
from simple_history.models import HistoricalRecords

from AppCore.core.exceptions.exceptions import NotFoundException


class BaseManager(Manager):
    _exception_class = None

    @property
    def exception_class(self):
        if self._exception_class is None:
            name = f"{self.model.__name__}NotFoundException"
            self._exception_class = type(
                name,
                (NotFoundException, self.model.DoesNotExist),
                {}
            )
        return self._exception_class

    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except self.model.DoesNotExist as e:
            raise self.exception_class(f"{self.model._meta.verbose_name} não encontrado.")


class BaseManagerUser(BaseUserManager, BaseManager):
    pass

class BasicModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(inherit=True)
    
    objects = BaseManager()

    class Meta:
        abstract = True
