from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from simple_history.admin import SimpleHistoryAdmin

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import (
    AuthorizationException,
    BusinessRuleException,
    NotFoundException,
    SystemErrorException,
    ValidationException,
)


def run_business(fn):
    """Executa callable da camada Business e converte exceções de domínio para o admin."""
    try:
        return fn()
    except ModelInstanceBusiness.exceptions_handled as exc:
        message = getattr(exc, 'message', str(exc))
        raise ValidationError(message) from exc
    except SystemErrorException as exc:
        raise ValidationError(exc.message) from exc


class CortexModelAdmin(SimpleHistoryAdmin):
    """Base do Django Admin alinhada ao AppCore (histórico, auditoria e soft delete)."""

    audit_readonly_fields = ('created_at', 'updated_at')
    allow_hard_delete = False

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        for field_name in self.audit_readonly_fields:
            if (
                field_name not in readonly
                and any(f.name == field_name for f in self.model._meta.fields)
            ):
                readonly.append(field_name)
        return readonly

    def has_delete_permission(self, request, obj=None):
        if not self.allow_hard_delete:
            return False
        return super().has_delete_permission(request, obj)



class AtivoModelAdmin(CortexModelAdmin):
    """Admin para entidades com campo `ativo` e métodos business de desativar/reativar."""

    list_filter = ('ativo',)
    actions = ('desativar_selecionados', 'reativar_selecionados')

    @admin.action(description='Desativar selecionados')
    def desativar_selecionados(self, request, queryset):
        for obj in queryset:
            try:
                run_business(lambda current=obj: current.business.desativar())
                self.message_user(request, f'{obj} desativado com sucesso.', messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, f'{obj}: {exc.message}', messages.ERROR)

    @admin.action(description='Reativar selecionados')
    def reativar_selecionados(self, request, queryset):
        for obj in queryset:
            try:
                run_business(lambda current=obj: current.business.reativar())
                self.message_user(request, f'{obj} reativado com sucesso.', messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, f'{obj}: {exc.message}', messages.ERROR)


class ReadOnlyModelAdmin(CortexModelAdmin):
    """Admin somente leitura para entidades gerenciadas por fluxos automatizados."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
