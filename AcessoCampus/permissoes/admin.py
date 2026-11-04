from django.contrib import admin

from AppCore.basics.admin import run_business

from .models import PermissaoFuncaoAcessoCampus, PermissaoUsuarioAcessoCampus


@admin.register(PermissaoFuncaoAcessoCampus)
class PermissaoFuncaoAcessoCampusAdmin(admin.ModelAdmin):
    list_display = (
        'funcao',
        'solicitar',
        'analisar_solicitacoes',
        'operar_portaria',
        'visualizar_historico',
    )
    list_filter = ('analisar_solicitacoes', 'operar_portaria', 'solicitar')
    search_fields = ('funcao__papel_funcao',)
    ordering = ('funcao__papel_funcao',)

    def save_model(self, request, obj, form, change):
        capacidades = {
            'solicitar': obj.solicitar,
            'analisar_solicitacoes': obj.analisar_solicitacoes,
            'operar_portaria': obj.operar_portaria,
            'visualizar_historico': obj.visualizar_historico,
        }
        if not change:
            created = run_business(
                lambda: PermissaoFuncaoAcessoCampus().business.criar_permissao(
                    funcao_id=obj.funcao_id,
                    **capacidades,
                )
            )
            obj.pk = created.pk
            return
        dados = {field: form.cleaned_data[field] for field in form.changed_data}
        if dados:
            run_business(lambda: obj.business.atualizar_capacidades(dados))


@admin.register(PermissaoUsuarioAcessoCampus)
class PermissaoUsuarioAcessoCampusAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'solicitar',
        'analisar_solicitacoes',
        'operar_portaria',
        'visualizar_historico',
    )
    search_fields = ('usuario__nome', 'usuario__cpf')
    autocomplete_fields = ('usuario',)

    def save_model(self, request, obj, form, change):
        capacidades = {
            'solicitar': obj.solicitar,
            'analisar_solicitacoes': obj.analisar_solicitacoes,
            'operar_portaria': obj.operar_portaria,
            'visualizar_historico': obj.visualizar_historico,
        }
        if not change:
            created = run_business(
                lambda: PermissaoUsuarioAcessoCampus().business.criar_permissao(
                    usuario_id=obj.usuario_id,
                    **capacidades,
                )
            )
            obj.pk = created.pk
            return
        dados = {field: form.cleaned_data[field] for field in form.changed_data}
        if dados:
            run_business(lambda: obj.business.atualizar_capacidades(dados))
