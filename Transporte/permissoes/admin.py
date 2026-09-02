from django.contrib import admin

from AppCore.basics.admin import run_business

from .models import PermissaoFuncaoTransporte, PermissaoUsuarioTransporte


@admin.register(PermissaoFuncaoTransporte)
class PermissaoFuncaoTransporteAdmin(admin.ModelAdmin):
    list_display = ('funcao', 'conferir', 'created_at')
    list_filter = ('conferir',)
    search_fields = ('funcao__papel_funcao', 'funcao__descricao')
    ordering = ('funcao__papel_funcao',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: PermissaoFuncaoTransporte().business.criar_permissao(
                    funcao_id=obj.funcao_id,
                    conferir=obj.conferir,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if dados:
            run_business(lambda: obj.business.atualizar_capacidades(dados))


@admin.register(PermissaoUsuarioTransporte)
class PermissaoUsuarioTransporteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'conferir', 'created_at')
    list_filter = ('conferir',)
    search_fields = ('usuario__nome', 'usuario__cpf', 'usuario__email')
    autocomplete_fields = ('usuario',)
    ordering = ('usuario__nome',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: PermissaoUsuarioTransporte().business.criar_permissao(
                    usuario_id=obj.usuario_id,
                    conferir=obj.conferir,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if dados:
            run_business(lambda: obj.business.atualizar_capacidades(dados))
