from django.contrib import admin
from django.core.exceptions import ValidationError

from AppCore.basics.admin import CortexModelAdmin, run_business

from .models import SetorVinculo


@admin.register(SetorVinculo)
class SetorVinculoAdmin(CortexModelAdmin):
    list_display = (
        'usuario',
        'setor',
        'funcao',
        'responsavel',
        'created_at',
    )
    list_filter = ('responsavel', 'setor', 'funcao', 'setor__ativo')
    search_fields = (
        'usuario__nome',
        'usuario__cpf',
        'setor__sigla',
        'setor__nome',
        'funcao__papel_funcao',
        'funcao__descricao',
    )
    autocomplete_fields = ('usuario', 'setor', 'funcao')
    ordering = ('setor__nome', 'usuario__nome')
    allow_hard_delete = True
    actions = ('encerrar_vinculos_selecionados',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('usuario', 'setor', 'funcao')
        )

    @admin.action(description='Encerrar vínculos selecionados')
    def encerrar_vinculos_selecionados(self, request, queryset):
        for vinculo in queryset:
            try:
                run_business(lambda current=vinculo: current.business.encerrar_vinculo())
            except ValidationError as exc:
                self.message_user(request, f'{vinculo}: {exc.message}', level='error')

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: SetorVinculo().business.criar_vinculo(
                    usuario=obj.usuario,
                    setor=obj.setor,
                    funcao=obj.funcao,
                    responsavel=obj.responsavel,
                )
            )
            obj.pk = created.pk
            return

        original = SetorVinculo.objects.get(pk=obj.pk)

        if 'funcao' in form.changed_data:
            run_business(lambda: obj.business.atualizar_funcao(obj.funcao))

        if 'responsavel' in form.changed_data:
            if obj.responsavel and not original.responsavel:
                run_business(lambda: obj.business.definir_como_responsavel())
            elif not obj.responsavel and original.responsavel:
                run_business(lambda: obj.business.remover_responsabilidade())

        outros_campos = {
            field
            for field in form.changed_data
            if field not in {'funcao', 'responsavel'}
        }
        if outros_campos:
            for field in outros_campos:
                setattr(obj, field, form.cleaned_data[field])
            obj.save()

    def delete_model(self, request, obj):
        run_business(lambda: obj.business.encerrar_vinculo())

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)
