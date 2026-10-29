from django.contrib import admin

from .models import Emprestimo, ItemEmprestimo, SolicitacaoTrocaTitular


class ItemEmprestimoInline(admin.TabularInline):
    model = ItemEmprestimo
    extra = 0
    raw_id_fields = ('recurso',)


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'responsavel', 'origem_conta_coletiva', 'retirada_em', 'created_at')
    list_filter = ('origem_conta_coletiva', 'retirada_em')
    search_fields = ('solicitante__nome', 'solicitante__cpf', 'observacao')
    raw_id_fields = ('solicitante', 'responsavel')
    readonly_fields = ('origem_conta_coletiva',)
    inlines = [ItemEmprestimoInline]
    ordering = ('solicitante__nome', '-retirada_em')


@admin.register(SolicitacaoTrocaTitular)
class SolicitacaoTrocaTitularAdmin(admin.ModelAdmin):
    list_display = ('id', 'emprestimo', 'solicitante', 'destinatario', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('solicitante__nome', 'destinatario__nome', 'observacao')
    raw_id_fields = ('emprestimo', 'solicitante', 'destinatario', 'novo_emprestimo')
    readonly_fields = ('respondido_em',)
