from django.contrib import admin

from .models import Emprestimo, ItemEmprestimo


class ItemEmprestimoInline(admin.TabularInline):
    model = ItemEmprestimo
    extra = 0
    raw_id_fields = ('recurso',)


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'responsavel', 'retirada_em', 'created_at')
    list_filter = ('retirada_em',)
    search_fields = ('solicitante__nome', 'solicitante__cpf', 'observacao')
    raw_id_fields = ('solicitante', 'responsavel')
    inlines = [ItemEmprestimoInline]
    ordering = ('solicitante__nome', '-retirada_em')
