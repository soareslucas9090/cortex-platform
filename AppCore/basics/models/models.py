from django.db import models
from django.db.models import Manager
from django.contrib.auth.models import BaseUserManager
from simple_history.models import HistoricalRecords

from AppCore.core.exceptions.exceptions import NotFoundException

_NOT_FOUND_EXCEPTION_CLASSES = {}


def _not_found_exception_class(model):
    cached = _NOT_FOUND_EXCEPTION_CLASSES.get(model)
    if cached is None:
        name = f"{model.__name__}NotFoundException"
        cached = type(name, (NotFoundException, model.DoesNotExist), {})
        _NOT_FOUND_EXCEPTION_CLASSES[model] = cached
    return cached


class BaseQuerySet(models.QuerySet):
    def get(self, *args, **kwargs):
        try:
            return super().get(*args, **kwargs)
        except self.model.DoesNotExist:
            raise _not_found_exception_class(self.model)(
                f"{self.model._meta.verbose_name} não encontrado.",
            )


class BaseManager(Manager):
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)


class BaseManagerUser(BaseUserManager, BaseManager):
    pass

class BasicModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(inherit=True)
    
    objects = BaseManager()

    class Meta:
        abstract = True
