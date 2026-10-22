from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import Envio, Notificacao


class EnvioInline(admin.TabularInline):
    model = Envio
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    readonly_fields = [
        'canal',
        'status',
        'destino',
        'tentativas',
        'ultimo_erro',
        'enviado_em',
        'created_at',
        'updated_at',
    ]
    fields = readonly_fields


@admin.register(Notificacao)
class NotificacaoAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'destinatario', 'tipo', 'titulo', 'lida_em', 'created_at']
    list_filter = ['tipo', 'lida_em']
    search_fields = ['titulo', 'corpo', 'destinatario__nome', 'destinatario__cpf']
    inlines = [EnvioInline]


@admin.register(Envio)
class EnvioAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'notificacao', 'canal', 'status', 'destino', 'tentativas', 'created_at']
    list_filter = ['canal', 'status']
    search_fields = ['destino', 'notificacao__titulo', 'ultimo_erro']
